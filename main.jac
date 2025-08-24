import from mtllm {Model}
import from utils {validate_github_url,is_path_valid_up_to_parent,dict_to_tree,message}
import os;
import from tools {get_repo_name_from_url,clone_repo_to_current_dir,load_gitignore,build_structure,get_folder_dict,extract_readmes,create_readme_file}
import from typing {Dict,Any}
import from pathspec {PathSpec}
import from build_tree_sitter {traverse_and_parse}

glob llm = Model(model_name = "gemini/gemini-2.0-flash");

enum AgentType
{
    MapperAgent = "MapperAgent",
    AnalyzerAgent = "AnalyzerAgent",
    DocGenie = "DocGenie"
}

node Agent
{
    has agent_type:AgentType;
}


node managerAgent
{
    has github_url:str = "";
    has message:str = message;
    has repo_path:str = "";

    """use to decide the next step of the agent"""
    def decide (message:str,chat_history:list[dict]) -> AgentType by llm(verbose=True,method="ReAct");

    """Tool to clone the repositories from the github"""
    def clone_github_repository(github_url:str,repo_path:str) -> str by llm(tools=[clone_repo_to_current_dir,get_repo_name_from_url],verbose=True,method="ReAct");

    """Generate a message about your actions to add to the chat_history"""
    def generate_chat_history_message(message:str) -> dict[str,str] by llm();

    can route with codeBaseGenius entry
    {
        if os.path.exists(self.repo_path)
        {
            response:AgentType = self.decide(self.message,visitor.get_last_five_messages());
            print(f"Navigating to {response}");
            
            chat_history_message:dict[str,str] = self.generate_chat_history_message(f"Navigating to {response}");
            visitor.chat_history.append(chat_history_message);

            visit[-->](`?Agent)(?agent_type==response);
        }
        else
        {
            repository_clone_message:str = self.clone_github_repository(self.github_url,self.repo_path);
            response:AgentType = self.decide(self.message,visitor.get_last_five_messages());
            print(f"Navigating to {response}");

            chat_history_message:dict[str,str] = self.generate_chat_history_message(repository_clone_message + f"Navigating to {response}");
            visitor.chat_history.append(chat_history_message);

            visit[-->](`?Agent)(?agent_type==response);
        }
    }
}

node repoMapperAgent(Agent)
{
    has agent_type:AgentType = AgentType.MapperAgent;
    has repo_path:str = "";

    """Generate a message about your actions to add to the chat_history"""
    def generate_chat_history_message(message:str) -> dict[str,str] by llm();

    """Generate summeries for readme.md files in a given code_structure"""
    def generate_readme_files_summeries(readme_contents:dict[str,str]) -> dict[str,str] by llm();

    can map_repo with codeBaseGenius entry
    {
        print("Building Repository Folder Structure...");
        gitignore:PathSpec = load_gitignore(self.repo_path);
        structure:Dict[str,Any] = build_structure(self.repo_path,gitignore);
        folders_dict:dict[str,str] = get_folder_dict(self.repo_path,gitignore);
        readme_contents:dict[str,str] = extract_readmes(structure);

        visitor.code_structure = structure;
        visitor.folders_dict = folders_dict;
        visitor.readme_contents = readme_contents;
        
        tree:str = dict_to_tree(structure);
        
        print("Generating README Files Summeries...");
        readme_file_summeries:dict[str,str] = self.generate_readme_files_summeries(readme_contents);

        chat_history_message:dict[str,str] = self.generate_chat_history_message(f"Generate the repo structure " + tree + "Generate summeries for readme.md files");
        visitor.chat_history.append(chat_history_message);

        visit[<--];
    }
}

node codeAnalyzerAgent(Agent)
{
    has agent_type:AgentType = AgentType.AnalyzerAgent;

    can analyze_code with codeBaseGenius entry
    {
        analysis:dict = traverse_and_parse(visitor.code_structure);
        print("Code Analysis Complete.");
        visitor.chat_history.append({"action":"Code Analysis Complete."});
        visitor.code_analysis = analysis;
    
        visit[<--];
    }
}

node docGenieAgent(Agent)
{
    has agent_type:AgentType = AgentType.DocGenie;
    has doc_path:str = "";

    def generate_readme_files_for_each_folder(folders_dict:dict[str,str],readme_summeries:dict[str,str],doc_path:str,code_analysis:dict) -> str by llm(tools=[create_readme_file],verbose=True,method="ReAct");

    can generate_docs with codeBaseGenius entry
    {
        if not os.path.exists(self.doc_path)
        {
            os.mkdir(self.doc_path);
            self.generate_readme_files_for_each_folder(visitor.folders_dict,visitor.readme_contents,self.doc_path,visitor.code_analysis);
            print("Documentation Generation Complete.");
        }
        else
        {
            self.generate_readme_files_for_each_folder(visitor.folders_dict,visitor.readme_contents,self.doc_path,visitor.code_analysis);
            print("Documentation Generation Complete.");
        }
    }
}

walker codeBaseGenius
{
    has chat_history:list[dict];
    has code_structure:Dict[str,Any] = {};
    has folders_dict:dict[str,str] = {};
    has readme_contents:dict[str,str] = {};
    has codde_analysis:dict = {};

    def get_last_five_messages() -> list[dict]
    {
        if(len(self.chat_history))>5
        {
            return self.chat_history[-5:];
        }
        else
        {
            return self.chat_history[:len(self.chat_history)];
        }
    }

}

with entry
{
    while True
    {
        github_url = input("Enter GitHub URL:");
        doc_path = input("Enter folder path to save documents(or keep blank to create a docs folder inside the repo):\n");

        repo_name:str = get_repo_name_from_url(github_url);
        repo_path:str = os.path.join(os.getcwd(),repo_name);

        if(len(doc_path) == 0)
        {
            doc_path = os.path.join(repo_path,"docs");
            print(f"Document path set to {doc_path}");
        }
        else
        {
            if not is_path_valid_up_to_parent(doc_path)
            {
                print("Invalid folder path");
                break;
            }
        }

        if not validate_github_url(github_url)
        {
            print("Invalid GitHub URL");
            break;
        }

        manager_agent = root++>managerAgent(github_url=github_url,repo_path=repo_path);
        manager_agent++>repoMapperAgent(repo_path=repo_path);
        manager_agent++>codeAnalyzerAgent();
        manager_agent++>docGenieAgent(doc_path=doc_path);

        manager_agent spawn codeBaseGenius([{"user":f"{github_url}"}]);
    }
}
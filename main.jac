import from mtllm {Model}
import from utils {validate_github_url,is_path_valid_up_to_parent}
import os;
import from tools {get_repo_name_from_url,clone_repo_to_current_dir}

glob llm = Model(model_name = "gemini/gemini-2.0-flash");

enum AgentType
{
    MapperAgent="MapperAgent",
    AnalyzerAgent="AnalyzerAgent",
    DocGenie="DocGenie"
}

node Agent
{
    has agent_type:AgentType;
}


node managerAgent
{
    has doc_path:str="";
    has github_url:str="";
    has message:str=f"As a supervisor agent your first task is to clone a github repository from provided {github_url} if first step is fulfiled if and only if then navigate to the next Agent using AgentType and stop the program.";
    has repo_path:str="";

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
            print(visitor.chat_history);

            visit[-->](`?Agent)(?agent_type==response);
        }
        else
        {
            repository_clone_message:str=self.clone_github_repository(self.github_url,self.repo_path);
            response:AgentType = self.decide(self.message,visitor.get_last_five_messages());
            print(f"Navigating to {response}");
            chat_history_message:dict[str,str] = self.generate_chat_history_message(repository_clone_message + f"Navigating to {response}");
            visitor.chat_history.append(chat_history_message);
            print(visitor.chat_history);

            visit[-->](`?Agent)(?agent_type==response);
        }
    }
}

node repoMapperAgent(Agent)
{
    has agent_type:AgentType=AgentType.MapperAgent;
    has repo_path:str="";
    has folder_structure:list[dict]=[];

    def get_dotgitignore_file_content(repo_path:str) -> list[str] by llm(methods="ReAct");

    can map_repo with codeBaseGenius entry
    {
    #    gitignore_path:str = load_gitignore(self.repo_path);
    #    gitignore_content:list[str] = self.get_dotgitignore_file_content(self.repo_path);
    #    print(gitignore_content);
    }
}

node codeAnalyzerAgent(Agent)
{
    has agent_type:AgentType=AgentType.AnalyzerAgent;

    can analyze_code with codeBaseGenius entry
    {
        print("analyzer");
        disengage;
    }
}

node docGenieAgent(Agent)
{
    has agent_type:AgentType=AgentType.DocGenie;
    has doc_path:str="";

    can generate_docs with codeBaseGenius entry
    {
        print("docgenie");
        disengage;
    }
}

walker codeBaseGenius
{
    has chat_history:list[dict];

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
        github_url=input("Enter GitHub URL:");
        doc_path=input("Enter folder path to save documents:");

        repo_name:str=get_repo_name_from_url(github_url);
        repo_path:str=os.path.join(os.getcwd(),repo_name);

        if not validate_github_url(github_url)
        {
            print("Invalid GitHub URL");
            break;
        }

        if not is_path_valid_up_to_parent(doc_path)
        {
            print("Invalid folder path");
            break;
        }

        manager_agent=root++>managerAgent(doc_path=doc_path,github_url=github_url,repo_path=repo_path);
        manager_agent++>repoMapperAgent(repo_path=repo_path);
        manager_agent++>codeAnalyzerAgent();
        manager_agent++>docGenieAgent(doc_path=doc_path);

        manager_agent spawn codeBaseGenius([{"user":f"{github_url}"}]);
    }
}
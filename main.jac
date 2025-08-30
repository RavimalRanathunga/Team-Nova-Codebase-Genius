import from mtllm {Model}
import from mtllm.types {Image}
import from utils {validate_github_url,is_path_valid_up_to_parent,dict_to_tree,message,generate_images_using_mermaid_diagrams,generate_code_structure_using_mermaid_diagrams,instruction_to_generate_code_structure_mermaid_diagram,instruction_to_generate_class_diagram_mermaid_diagram,instruction_to_generate_sequence_diagram_mermaid_diagram}
import os;
import from tools {get_repo_name_from_url,clone_repo_to_current_dir,load_gitignore,build_structure,get_folder_dict,extract_readmes,create_readme_file,update_main_readme,get_links_of_generated_readmes,get_links_of_generated_images}
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

    can route with codeBaseGenius entry;
}

node repoMapperAgent(Agent)
{
    has agent_type:AgentType = AgentType.MapperAgent;
    has repo_path:str = "";

    """Generate summeries for readme.md files in a given code_structure"""
    def generate_readme_files_summeries(readme_contents:dict[str,str]) -> dict[str,str] by llm();

    can map_repo with codeBaseGenius entry;
}

node codeAnalyzerAgent(Agent)
{
    has agent_type:AgentType = AgentType.AnalyzerAgent;

    can analyze_code with codeBaseGenius entry;
}

node docGenieAgent(Agent)
{
    has agent_type:AgentType = AgentType.DocGenie;
    has doc_path:str = "";

    """Generaete a README file in markdown format for each folder in the repository using the provided code_analysis and readme_summeries and save in provided doc_path.readme content must contain all insightful information about all files,classes and functions in a selected folder with image of a file structure inside the folder"""
    def generate_readme_files_for_each_folder(folders_dict:dict[str,str],readme_summeries:dict[str,str],doc_path:str,code_analysis:dict,code_structure:str,instruction_to_generate_code_structure_mermaid_diagram:str) -> str by llm(tools=[create_readme_file,generate_code_structure_using_mermaid_diagrams,get_links_of_generated_images],verbose=True,method="ReAct");

    """Generate a class diagram using mermaid diagrams and save it as an image in the specified path"""
    def generate_class_diagram_as_an_image(doc_path:str,code_analysis:dict,instruction_to_generate_class_diagram_mermaid_diagram:str) -> str by llm(tools=[generate_images_using_mermaid_diagrams],verbose=True,method="ReAct");

    """Generate a sequence diagram using mermaid diagrams and save it as an image in the specified path"""
    def generate_sequence_diagram_as_an_image(doc_path:str,code_analysis:dict,instruction_to_generate_sequence_diagram_mermaid_diagram:str) -> str by llm(tools=[generate_images_using_mermaid_diagrams],verbose=True,method="ReAct");

    """Update the main README file in markdown format to include links to all generated README files and a summary of main readme file in the repository and generated images and save the file in the doc_path"""
    def update_main_readme(doc_path:str,readme_summeries:dict[str,str]) -> str by llm(tools=[update_main_readme,get_links_of_generated_readmes,get_links_of_generated_images],method="ReAct");

    can generate_docs with codeBaseGenius entry;
    
}

walker codeBaseGenius
{
    has chat_history:list[dict];
    has code_structure:Dict[str,Any] = {};
    has folders_dict:dict[str,str] = {};
    has readme_contents:dict[str,str] = {};
    has code_analysis:dict = {};

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
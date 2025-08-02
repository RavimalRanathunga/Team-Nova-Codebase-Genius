import from mtllm {Model}
import from utils {validate_github_url,is_path_valid_up_to_parent}
import os;
import from git {Repo}

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


"""
Tool to get repo name from a given github URL
Example input to the tool
{"github_url":"github_url"} 
"""
def get_repo_name_from_url(github_url:str) -> str
{
        return github_url.rstrip("/").split("/")[-1].replace(".git", "");
}

"""
use this tool to clone a github repository
Example input to the tool
{"github_url":"github_url","repo_path","repo_path","repo_name","repo_name"}
"""
def clone_repo_to_current_dir(github_url:str,repo_path:str,repo_name:str) -> str
{
    if os.path.exists(repo_path)
    {
        return (f"Repository '{repo_name}' already exists in current directory.");
    }
    else
    {
        print(f"Cloning '{repo_name}' into current directory...");
        Repo.clone_from(github_url, repo_path);
        print("Cloning complete.");
    }
    return repo_path;
}

node managerAgent
{
    has doc_path:str="";
    has github_url:str="";
    has message:str=f"As a supervisor agent your first task is to clone a github repository from provided {github_url} if first step is fulfiled if and only if then navigate to the next Agent using AgentType and stop the program.";
    has repo_path:str=os.getcwd();

    """use to decide the next step of the agent"""
    def decide (message:str) -> AgentType by llm(verbose=True,method="ReAct");
    def clone_github_repository(github_url:str,repo_path:str) -> str by llm(tools=[clone_repo_to_current_dir,get_repo_name_from_url],verbose=True,method="ReAct");

    can route with codeBaseGenius entry
    {
        print(self.clone_github_repository(self.github_url,self.repo_path));
        response:AgentType = self.decide(self.message);
        visit[-->](`?Agent)(?agent_type==response);
    }
}

node repoMapperAgent(Agent)
{
    has agent_type:AgentType=AgentType.MapperAgent;

    can map_repo with codeBaseGenius entry
    {
       print("repomapper");
       disengage;
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
    manager_agent++>repoMapperAgent();
    manager_agent++>codeAnalyzerAgent();
    manager_agent++>docGenieAgent(doc_path=doc_path);

    manager_agent spawn codeBaseGenius([{"user":f"{github_url}"}]);
    }
}
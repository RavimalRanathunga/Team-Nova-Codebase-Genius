node managerAgent
{
    has folder_path:str="";
    has github_url:str="";

}

node repoMapperAgent 
{
  
}

node codeAnalyzerAgent
{

}

node docGenieAgent
{

}

walker codeBaseGenius
{
    has chat_history:list[dict];

    can route with managerAgent entry
    {
        
    }

    can map_repo with repoMapperAgent entry
    {
       
    }

    can analyze_code with codeAnalyzerAgent entry
    {

    }

    can generate_docs with docGenieAgent entry
    {
        
    }
}

with entry
{
    github_url=input("Enter GitHub URL:");
    folder_path=input("Enter folder path to clone the repository:");

    manager_agent=root++>managerAgent(folder_path=folder_path,github_url=github_url);

    manager_agent spawn codeBaseGenius([{"user":f"{github_url}"}]);
}
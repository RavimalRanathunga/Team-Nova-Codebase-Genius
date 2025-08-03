import os;
import from git {Repo}

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
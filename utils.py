import re
from pathlib import Path
import os
from git import Repo

def get_repo_name_from_url(repo_url) -> str:
    return repo_url.rstrip("/").split("/")[-1].replace(".git", "")

def clone_repo_to_current_dir(repo_url) -> str:
    repo_name = get_repo_name_from_url(repo_url)
    target_path = os.path.join(os.getcwd(), repo_name)

    if os.path.exists(target_path):
        return (f"Repository '{repo_name}' already exists in current directory.")
    else:
        print(f"Cloning '{repo_name}' into current directory...")
        Repo.clone_from(repo_url, target_path)
        print("Cloning complete.")
    
    return target_path

def is_path_valid_up_to_parent(path: str) -> bool:
    """
    Checks if all intermediate directories in the given path exist, 
    excluding the last folder (which can be created).
    """
    parent_path = Path(path).parent
    return parent_path.exists() and parent_path.is_dir()

def validate_github_url(url):
    """
    Validates that the URL is a properly formatted GitHub repository URL.
    """
    pattern = r"^https:\/\/github\.com\/[\w\-\.]+\/[\w\-\.]+(\.git)?$"
    return re.match(pattern, url) is not None


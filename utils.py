import re
from pathlib import Path
import os

def is_path_valid_up_to_parent(path: str) -> bool:
    """
    Checks if all intermediate directories in the given path exist, 
    excluding the last folder (which can be created).
    """
    pattern = r"^[a-zA-Z]:\\(?:[^\\/:*?\"<>|\r\n]+\\?)*$"

    if  re.match(pattern, path):
        parent_path = Path(path).parent
        return parent_path.exists() and parent_path.is_dir()
    else:
        return False

def validate_github_url(url):
    """
    Validates that the URL is a properly formatted GitHub repository URL.
    """
    pattern = r"^https:\/\/github\.com\/[\w\-\.]+\/[\w\-\.]+(\.git)?$"
    return re.match(pattern, url) is not None

def dict_to_tree(structure: dict, indent: str = "") -> str:
    """Convert the nested structure_dict into a folder tree string."""
    tree_str = ""
    for i, (name, content) in enumerate(structure.items()):
        is_last = i == len(structure) - 1
        prefix = "└── " if is_last else "├── "

        if isinstance(content, dict):
            # Folder
            tree_str += f"{indent}{prefix}{name}/\n"
            # Recurse into subfolder
            tree_str += dict_to_tree(content, indent + ("    " if is_last else "│   "))
        else:
            # File
            tree_str += f"{indent}{prefix}{name}\n"

    return tree_str


message = """
            As a supervisor agent your first task is to clone a github repository from provided {github_url} if first step is fulfiled if and only if then navigate to the next Agent using AgentType.
            Your ultimate goal is to create comprehensive and complete documentatio for a repository in a given {github_url}
            You should decide which Agent to visit next based on the provided {chat_history} and the progress toward your ultimate goal.
            The main responsibilities of each Agent as follows:
                1.repoMapperAgent - Maps the repository folder structure and generate small summaries of readme.md files.
                2.codeAnalyzerAgent - Analyze the relationships between modules,classes and functions in the repository for that agent will use the folder structure from repoMapperAgent.
                3.docGenieAgent - Generate comprehensive and complete documentation of the repository.
            
          """
import re
from pathlib import Path

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


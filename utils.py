import re
from pathlib import Path
import os
import base64
import io, requests
from IPython.display import Image, display
from PIL import Image as im
import matplotlib.pyplot as plt

def is_path_valid_up_to_parent(path: str) -> bool:
    """
    Checks if all intermediate directories in the given path exist, 
    excluding the last folder (which can be created).
    """
    pattern = r"^[a-zA-Z]:\\(?:[^\\/:*?\"<>|\r\n]+\\?)*$"

    if  re.match(pattern, path):
        parent_path = Path(path).parent
        parent_path_exists = parent_path.exists() and parent_path.is_dir()

        if parent_path_exists:
            if os.path.exists(path):
                return True
            else:
                os.mkdir(path)
                return True
        
        return parent_path_exists
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


def generate_images_using_mermaid_diagrams(structure:str,doc_path:str,image_name:str) -> None:
    graphbytes = structure.encode("utf8")
    base64_bytes = base64.urlsafe_b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")
    img = im.open(io.BytesIO(requests.get('https://mermaid.ink/img/' + base64_string).content))
    plt.imshow(img)
    plt.axis('off') # allow to hide axis
    plt.savefig(f'{doc_path}/{image_name}.png', dpi=300, bbox_inches='tight')

def generate_code_structure_using_mermaid_diagrams(structure:str,doc_path:str,folder_name:str) -> None:
    graphbytes = structure.encode("utf8")
    base64_bytes = base64.urlsafe_b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")
    img = im.open(io.BytesIO(requests.get('https://mermaid.ink/img/' + base64_string).content))
    plt.imshow(img)
    plt.axis('off') # allow to hide axis
    plt.savefig(f'{doc_path}/{folder_name}.png', dpi=300, bbox_inches='tight')

message = """
            As a supervisor agent your first task is to clone a github repository from provided {github_url} if first step is fulfiled if and only if then navigate to the next Agent using AgentType.
            Your ultimate goal is to create comprehensive and complete documentatio for a repository in a given {github_url}
            You should decide which Agent to visit next based on the provided {chat_history} and the progress toward your ultimate goal.
            The main responsibilities of each Agent as follows:
                1.repoMapperAgent - Maps the repository folder structure and generate small summaries of readme.md files.
                2.codeAnalyzerAgent - Analyze the relationships between modules,classes and functions in the repository for that agent will use the folder structure from repoMapperAgent.
                3.docGenieAgent - Generate comprehensive and complete documentation of the repository.
          """

instruction_to_generate_code_structure_mermaid_diagram = """
        Generate a mermaid diagram that represents the folder and file structure of a specific folder.The input formats to the {generate_code_structure_using_mermaid_diagrams} function should be a strings for {structure} and {doc_path} and {folder_name}.
        The {structure} should be a string representation of the folder structure in mermaid format.
        The Example format of the {structure} is as follows:
        graph TD;
            A[Root] --> B[Folder1];
            A --> C[Folder2];
            B --> D[File1.py];
            B --> E[File2.py];
            C --> F[Subfolder1];
            F --> G[File3.py];
            C --> H[File4.py];
        The {doc_path} should be the path where the generated diagram image will be saved.
        The {folder_name} should be the name of the folder considering to generated diagram image without extension.
        """

instruction_to_generate_class_diagram_mermaid_diagram = """
        Generate a mermaid diagram that represents the class structure of the repository.The input formats to the {generate_images_using_mermaid_diagrams} function should be a strings for {structure} and {path} and {image_name}.
        The {structure} should be a string representation of the class structure in mermaid format.
        The Example format of the {structure} is as follows:
        classDiagram
            class Animal {
                +String name
                +int age
                +void makeSound()
                }
            class Dog {
                +String breed
                +void fetch()
                }
            Animal <|-- Dog
        Other available claas relationship indicators are as follows:
            --|> : Inheritance
            *-- : Composition
            .. : Dependency
            --> : Association
            ..> : Dependency
            ..|> : Realization
            o-- : Aggregation
        The {path} should be the path where the generated diagram image will be saved.
        The {image_name} should be the name of the generated diagram image without extension.
        """

instruction_to_generate_sequence_diagram_mermaid_diagram = """
        Generate a mermaid diagram that represents the sequence of interactions between different components or objects in the repository.The input formats to the {generate_images_using_mermaid_diagrams} function should be a strings for {structure} and {path} and {image_name}.
        The {structure} should be a string representation of the sequence diagram in mermaid format.
        The Example format of the {structure} is as follows:
        sequenceDiagram
            participant User
            participant AuthService
            participant Database
            User->>AuthService: Login request
            AuthService->>Database: Query user credentials
            Database-->>AuthService: Return credentials
            AuthService-->>User: Login response
        The {path} should be the path where the generated diagram image will be saved.
        The {image_name} should be the name of the generated diagram image without extension.
        """
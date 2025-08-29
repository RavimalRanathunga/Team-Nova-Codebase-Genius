import os;
import from git {Repo}
import from typing {Dict,Any}
import from pathspec {PathSpec}

"""
Tool to get repo name from a given github URL
Example input to the tool
{"github_url":"github_url"}
Example output from the tool - repo_name:str 
"""
def get_repo_name_from_url(github_url:str) -> str
{
        return github_url.rstrip("/").split("/")[-1].replace(".git", "");
}

"""
use this tool to clone a github repository
Example input to the tool
{"github_url":"github_url","repo_path","repo_path","repo_name","repo_name"}
Example output from the tool - repo_path:str
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


"""Load .gitignore patterns if available.
Example input to the tool
{"repo_path":"repo_path"}
Example output from the tool - spec:PathSpec
"""
def load_gitignore(repo_path: str) -> PathSpec
{
    gitignore_path = os.path.join(repo_path, ".gitignore");
    if os.path.exists(gitignore_path)
    {
        with open(gitignore_path, "r") as f
        {
            return PathSpec.from_lines("gitwildmatch", f.readlines());
        }
    }
    return PathSpec.from_lines("gitwildmatch", []);
}

"""
Recursively build folder structure dictionary ignoring .gitignore files/folders.
Example input to the tool
{"repo_path":"repo_path","spec":PathSpec}
Example output from the tool - structure:Dict[str,Any]
"""
def build_structure(
    repo_path: str, 
    spec: PathSpec
) -> Dict[str,Any]
{
    structure = {};

    for item in os.listdir(repo_path)
    {
        item_path = os.path.join(repo_path, item);
        rel_path = os.path.relpath(item_path, repo_path);

        # Skip ignored files/folders
        if spec.match_file(rel_path)
        {
            continue;
        }

        if os.path.isdir(item_path)
        {
            # Recursively build sub-structure
            structure[item] = build_structure(item_path, spec);
        }
        else
        {
            # Store file with type and path
            if item.lower() == "readme.md" or item.lower() == "readme"
            {
                structure[item] = ["readme_file", item_path];
            }
            else
            {
                structure[item] = ["file", item_path];
            }
        }
    }

    return structure;
}

"""Get folder paths for a repo
Example input to the tool
{"repo_path":"repo_path","spec":PathSpec}
Example output from the tool - folders_dict:dict[str,str]
"""
def get_folder_dict(repo_path:str,spec:PathSpec) -> dict[str,str]
{
    folders_dict = {};
    structure = {};

    for item in os.listdir(repo_path)
    {
        item_path = os.path.join(repo_path, item);
        rel_path = os.path.relpath(item_path, repo_path);

        # Skip ignored files/folders
        if spec.match_file(rel_path)
        {
            continue;
        }

        if os.path.isdir(item_path)
        {
            # Add to folders dictionary
            folders_dict[item] = item_path;

            # Recursively build sub-structure
            structure[item] = build_structure(item_path, spec);
        }
        else
        {
            continue;
        }
    }

    return folders_dict;

}

"""
Tool to traverse structure dictionary to find readme files and return their content.
Example input to the tool
{"structure":Dict[str,Any]}
Example output from the tool - readme_contents:dict[str,str]
"""
def extract_readmes(structure: Dict[str,Any]) -> dict[str,str]
{

    readme_contents:dict[str,str] = {};

    def traverse(substruct: Dict[str,Any]) -> None
    {
        for (name, value) in substruct.items() 
        {
            if isinstance(value, Dict)
            {
                # Recurse into subfolder
                traverse(value);
            }
            else
            {
                # value = ["file/readme", path]
                ftype:str = value[0];
                path:str = value[1];
                if ftype == "readme_file"
                {
                    try
                    {
                        with open(path, "r", encoding="utf-8") as f
                        {
                            readme_contents[path] = f.read();
                        }
                    }
                    except Exception as e
                    {
                        readme_contents[path] = f"Error reading file: {e}";
                    }
                }
            }
        }
    }

    traverse(structure);
    return readme_contents;
}

"""Tool to create a README file in the specified path with given content
Example input to the tool
{"doc_path":"doc_path","content":"content","folder_name":"folder_name"}
Example output from the tool - path:str
"""
def create_readme_file(doc_path:str,content:str,folder_name:str) -> str
{
    path = os.path.join(doc_path, f"{folder_name}_README.md");
    print(f"Creating README file at: {path}");
    with open(path,"w",encoding="utf-8") as f
    {
        f.write(content);
    }

    return path;
}

"""Tool to update the main README file in the specified path with links to all generated README files and their summaries
Example input to the tool
{"doc_path":"doc_path","content":"content"}
Example output from the tool - path:str
"""
def update_main_readme(doc_path:str,content:str) -> str
{
    path = os.path.join(doc_path, "_MAIN_README.md");
    print(f"Updating MAIN README file at: {path}");
    with open(path,"w",encoding="utf-8") as f
    {
        f.write(content);
    }

    return path;
}

"""Tool to get links of all generated README files in the specified doc_path
Example input to the tool
{"doc_path":"doc_path"}
Example output from the tool - links:list[str]
"""
def get_links_of_generated_readmes_and_images(doc_path:str) -> list[str]
{
    links = [];
    for file in os.listdir(doc_path)
    {
        if file.endswith("_README.md") and file != "_MAIN_README.md"
        {
            links.append(file);
        }
    }
    return links;
}


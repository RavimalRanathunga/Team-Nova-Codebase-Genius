# Team Nova Codebase Genius

Team Nova Codebase Genius is an automated documentation generator for Python GitHub repositories, built using Jaclang and Python. It leverages multi-agent collaboration and large language models (LLMs) to analyze codebases and produce comprehensive documentation, including code structure, relationships, and visual diagrams.

## Features

- **Repository Cloning:** Clone any public GitHub repository for analysis.
- **Structure Mapping:** Automatically maps folder structure, respecting `.gitignore` rules.
- **Readme Summarization:** Extracts and summarizes all README files in the repository.
- **Code Analysis:** 
  - Identifies modules, classes, functions, and their line numbers.
  - Detects function calls and relationships.
  - Classifies imports as internal or external.
- **Documentation Generation:** Produces complete documentation for the repository, including Mermaid diagrams for folder and class structures.

## Agents

- **managerAgent:** Supervises workflow and agent coordination.
- **repoMapperAgent:** Maps repository structure and summarizes README files.
- **codeAnalyzerAgent:** Analyzes code relationships, imports, function calls, and architecture.
- **docGenieAgent:** Generates comprehensive documentation and diagrams.

## Usage

### 1. Create a Virtual Environment

It is recommended to use a Python virtual environment to manage dependencies:

```sh
python -m venv venv
```

Activate the environment:

- **Windows:**
  ```sh
  venv\Scripts\activate
  ```
- **Linux/macOS:**
  ```sh
  source venv/bin/activate
  ```

### 2. Install dependencies

```sh
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root required by agents and LLM integrations.  
Example `.env` content:

```
API_KEY=your_api_key_here
```

change the model name in the main.jac according to your LLM provider and model being used.
Refer to Jaseci documentation to find supported models.

### 4. Run the main program

```sh
jac run main.jac
```

### 5. Follow prompts

- Enter the GitHub repository URL.
- Specify the folder path to save documentation (or leave blank for create a docs folder inside the repository).

## Project Structure

- `main.jac`: Main Jaclang file orchestrating agent workflow.
- `tools.jac`: Utility functions for repository operations, structure mapping, and agent operations.
- `utils.py`: Python helpers for path validation, URL checking, and tree formatting.
- `build_tree_sitter.py`: Python code for parsing code structure, extracting classes, functions, imports, and function calls.
- `requirements.txt`: Python dependencies.
- `.gitignore`: Files and folders to ignore.
- `README.md`: Project documentation.

## Requirements

- Jaclang
- Python 3.10+
- See `requirements.txt` for all dependencies.

## How It Works

1. **Clone:** The manager agent clones the specified GitHub repository.
2. **Map:** The repoMapperAgent builds the folder structure and summarizes README files.
3. **Analyze:** The codeAnalyzerAgent examines code relationships, imports, and function calls.
4. **Document:** The docGenieAgent generates documentation and visual diagrams in the specified folder.

## Output

- Markdown documentation for each folder and module.
- Mermaid diagrams for folder and class structures.
- Summaries of README files.
- Listings of classes, functions, imports, and function calls with line numbers.

---

*Automate and streamline documentation for Python GitHub repositories using advanced agent-based techniques
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

1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
2. **Run the main program:**
   ```sh
   jac run main.jac
   ```
3. **Follow prompts:**
   - Enter the GitHub repository URL.
   - Specify the folder path to save documentation (or leave blank for default).

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

*Automate and streamline documentation for Python GitHub repositories using advanced agent-based techniques and
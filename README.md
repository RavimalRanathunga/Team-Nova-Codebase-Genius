# Team Nova Codebase Genius

Team Nova Codebase Genius is an automated documentation generator for GitHub repositories, built using Jaclang and Python. It utilizes multi-agent collaboration and large language models (LLMs) to analyze codebases and produce comprehensive documentation.

## Features

- **Repository Cloning:** Clone any public GitHub repository for analysis.
- **Structure Mapping:** Automatically maps folder structure, respecting `.gitignore` rules.
- **Readme Summarization:** Extracts and summarizes all README files in the repository.
- **Code Analysis:** Analyzes relationships between modules, classes, and functions.
- **Documentation Generation:** Produces complete documentation for the repository.

## Agents

- **repoMapperAgent:** Maps repository structure and summarizes README files.
- **codeAnalyzerAgent:** Analyzes code relationships and architecture.
- **docGenieAgent:** Generates comprehensive documentation.

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
- `tools.jac`: Utility functions for repository operations, structure mapping and for Agent operations.
- `utils.py`: Python helpers for path validation, URL checking, and tree formatting.
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
3. **Analyze:** The codeAnalyzerAgent examines code relationships.
4. **Document:** The docGenieAgent generates documentation in the specified folder.


*Automate and streamline documentation for any GitHub repository using advanced agent
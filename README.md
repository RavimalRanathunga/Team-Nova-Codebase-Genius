# Team Nova Codebase Genius

Team Nova Codebase Genius is an automated documentation generator for Python GitHub repositories, built entirely in Jac. It leverages multi-agent collaboration and large language models (LLMs) to analyze codebases and produce comprehensive documentation, including code structure, relationships, and visual diagrams.

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

### 1. Install the Jac toolchain

Jac ships as a single self-contained binary (no Python/pip install needed for the toolchain itself):

```sh
curl -fsSL https://raw.githubusercontent.com/jaseci-labs/jaseci/main/scripts/install.sh | bash
```

### 2. Install project dependencies

Python dependencies are declared in `jac.toml` (`[dependencies]`) instead of `requirements.txt`:

```sh
jac install
```

### 3. Set up environment variables

Create a `.env` file in the project root required by agents and LLM integrations.  
Example `.env` content:

```
API_KEY=your_api_key_here
```

Change the model name in `jac.toml` (`[byllm.model]`) or `main.jac` according to your LLM provider and model being used.
Refer to the [byLLM reference](https://docs.jaseci.org/reference/plugins/byllm/) to find supported models.

### 4. Run the main program

```sh
jac run main.jac
```

### 5. Follow prompts

- Enter the GitHub repository URL.
- Specify the folder path to save documentation (or leave blank for create a docs folder inside the repository).

## Project Structure

- `main.jac`: Main Jac file orchestrating agent workflow.
- `tools.jac`: Utility functions for repository operations, structure mapping, and agent operations.
- `utils.jac`: Helpers for path validation, URL checking, mermaid diagram rendering, and tree formatting.
- `build_tree_sitter.jac`: Parses code structure, extracting classes, functions, imports, and function calls with Tree-sitter.
- `jac.toml`: Project manifest and Python dependencies.
- `.gitignore`: Files and folders to ignore.
- `README.md`: Project documentation.

## Requirements

- Jac 0.34.17+
- See `jac.toml` for all dependencies.

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
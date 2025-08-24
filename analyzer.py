import os
import json
import networkx as nx
from pathlib import Path
from typing import Dict, Any
import google.generativeai as genai

# loading AST JSONs

def load_asts(index_path: Path):
    
    asts = {}
    
    with open(index_path, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            
            if (rec["ok"] and rec["ast_json_path"]):
                with open(rec["ast_json_path"], "r", encoding="utf-8") as af:
                    asts[rec["path"]] = json.load(af)
    
    return asts


def extract_abstractions(ast_dict: Dict[str, Any], abstractions: Dict[str, Any], file: str):
    if not isinstance(ast_dict, dict):
        return
    if ast_dict.get("_type") == "ClassDef":
        abstractions[file].append({"type": "class", "name": ast_dict.get("name")})
    elif ast_dict.get("_type") == "FunctionDef":
        abstractions[file].append({"type": "function", "name": ast_dict.get("name")})
    for k, v in ast_dict.items():
        if isinstance(v, (dict, list)):
            extract_abstractions(v, abstractions, file)


def build_dependency_graph(abstractions: Dict[str, Any]):
    G = nx.DiGraph()
    for file, items in abstractions.items():
        for item in items:
            node = f"{file}:{item['name']}"
            G.add_node(node, **item)
            # Example: add fake dependency to demo (later detect calls/imports)
            if item["type"] == "function" and "main" in item["name"].lower():
                G.add_edge(node, f"{file}:core")
    return G

# ---- Step 4: Send to Gemini for analysis ---- #
def analyze_with_llm(abstractions: Dict[str, Any]):
    prompt = "You are analyzing a codebase. Here are the abstractions:\n\n"
    for file, items in abstractions.items():
        prompt += f"\nFile: {file}\n"
        for item in items:
            prompt += f"  - {item['type'].capitalize()}: {item['name']}\n"
    prompt += "\nIdentify the core abstractions, architectural patterns, and relationships.\n"

    # Configure Gemini API (make sure API key is set in your environment)
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    return response.text if response else "[No response from Gemini]"

# ---- Main pipeline ---- #
def main():
    base = Path("./artifacts/say_hello-ast")  # <-- Change to match your repo's AST output folder
    index_path = base / "index.jsonl"

    asts = load_asts(index_path)
    abstractions = {file: [] for file in asts}

    for file, ast_dict in asts.items():
        extract_abstractions(ast_dict, abstractions, file)

    G = build_dependency_graph(abstractions)
    print(f"Dependency graph has {len(G.nodes)} nodes and {len(G.edges)} edges.")

    analysis = analyze_with_llm(abstractions)
    print("\n=== Gemini Analysis ===")
    print(analysis)

if __name__ == "__main__":
    main()

import os
import json
import networkx as nx
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
import google.generativeai as genai

# Loading AST JSONs
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
    """Extract classes and functions from AST"""
    if not isinstance(ast_dict, dict):
        return
    if ast_dict.get("_type") == "ClassDef":
        abstractions[file].append({
            "type": "class", 
            "name": ast_dict.get("name"),
            "lineno": ast_dict.get("lineno")
        })
    elif ast_dict.get("_type") == "FunctionDef":
        abstractions[file].append({
            "type": "function", 
            "name": ast_dict.get("name"),
            "lineno": ast_dict.get("lineno")
        })
    for k, v in ast_dict.items():
        if isinstance(v, (dict, list)):
            extract_abstractions(v, abstractions, file)

def extract_imports(ast_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract import statements from AST"""
    imports = []
    
    def process_node(node):
        if not isinstance(node, dict):
            return
        
        # Handle Import statements
        if node.get("_type") == "Import":
            for name_node in node.get("names", []):
                imports.append({
                    "type": "import",
                    "module": name_node.get("name"),
                    "alias": name_node.get("asname"),
                    "lineno": name_node.get("lineno")
                })
        
        # Handle ImportFrom statements
        elif node.get("_type") == "ImportFrom":
            module = node.get("module")
            for name_node in node.get("names", []):
                imports.append({
                    "type": "importfrom",
                    "module": module,
                    "name": name_node.get("name"),
                    "alias": name_node.get("asname"),
                    "lineno": name_node.get("lineno")
                })
        
        # Process children
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, (dict, list)):
                    process_node(v)
        elif isinstance(node, list):
            for item in node:
                process_node(item)
    
    process_node(ast_dict)
    return imports

def extract_function_calls(ast_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract function calls from AST"""
    calls = []
    
    def process_node(node):
        if not isinstance(node, dict):
            return
        
        if node.get("_type") == "Call":
            func = node.get("func", {})
            
            # Direct function call
            if func.get("_type") == "Name":
                calls.append({
                    "type": "call",
                    "name": func.get("id"),
                    "lineno": func.get("lineno")
                })
            # Method call (obj.method())
            elif func.get("_type") == "Attribute":
                calls.append({
                    "type": "method_call",
                    "object": get_object_name(func.get("value")),
                    "method": func.get("attr"),
                    "lineno": func.get("lineno")
                })
        
        # Process children
        for k, v in node.items():
            if isinstance(v, (dict, list)):
                process_node(v)
    
    def get_object_name(node):
        if not node:
            return "unknown"
        if node.get("_type") == "Name":
            return node.get("id", "unknown")
        return "complex_expr"
    
    process_node(ast_dict)
    return calls

def build_codebase_graph(asts: Dict[str, Any]) -> nx.DiGraph:
    """Build a graph representing the codebase structure and dependencies"""
    G = nx.DiGraph()
    
    # First, extract all abstractions
    abstractions = {file: [] for file in asts}
    imports_by_file = {}
    calls_by_file = {}
    
    for file, ast_dict in asts.items():
        extract_abstractions(ast_dict, abstractions, file)
        imports_by_file[file] = extract_imports(ast_dict)
        calls_by_file[file] = extract_function_calls(ast_dict)
    
    # Add nodes for files and their abstractions
    for file, items in abstractions.items():
        file_node = f"FILE:{file}"
        G.add_node(file_node, type="file", name=file)
        
        for item in items:
            abs_node = f"{item['type'].upper()}:{file}:{item['name']}"
            G.add_node(abs_node, **item)
            # Connect abstractions to their containing file
            G.add_edge(file_node, abs_node, type="contains")
    
    # Add edges for imports
    for file, imports in imports_by_file.items():
        file_node = f"FILE:{file}"
        for imp in imports:
            if imp["type"] == "importfrom":
                # Try to find the module being imported from
                target_file = find_module_file(imp["module"], asts.keys())
                if target_file:
                    target_node = f"FILE:{target_file}"
                    G.add_edge(file_node, target_node, type="imports_from", item=imp["name"])
                    
                    # Try to connect specific import to specific abstraction
                    for abs_item in abstractions.get(target_file, []):
                        if abs_item["name"] == imp["name"]:
                            abs_node = f"{abs_item['type'].upper()}:{target_file}:{abs_item['name']}"
                            imp_node = f"IMPORT:{file}:{imp['name']}"
                            G.add_node(imp_node, **imp)
                            G.add_edge(file_node, imp_node, type="directly_imports")
                            G.add_edge(imp_node, abs_node, type="references")
    
    # Add edges for function calls
    for file, calls in calls_by_file.items():
        file_node = f"FILE:{file}"
        for call in calls:
            # Try to find where the called function is defined
            if call["type"] == "call":
                # Find in imports and local definitions
                for imported_file in get_imports_for_file(file, imports_by_file):
                    for abs_item in abstractions.get(imported_file, []):
                        if abs_item["name"] == call["name"]:
                            call_node = f"CALL:{file}:{call['name']}:{call['lineno']}"
                            abs_node = f"{abs_item['type'].upper()}:{imported_file}:{abs_item['name']}"
                            G.add_node(call_node, **call)
                            G.add_edge(file_node, call_node, type="contains_call")
                            G.add_edge(call_node, abs_node, type="calls")
                
                # Check local definitions
                for abs_item in abstractions.get(file, []):
                    if abs_item["name"] == call["name"]:
                        call_node = f"CALL:{file}:{call['name']}:{call['lineno']}"
                        abs_node = f"{abs_item['type'].upper()}:{file}:{abs_item['name']}"
                        G.add_node(call_node, **call)
                        G.add_edge(file_node, call_node, type="contains_call")
                        G.add_edge(call_node, abs_node, type="calls")
    
    return G

def find_module_file(module: str, file_paths: List[str]) -> str:
    """Find a file that might define the given module"""
    # Try direct match
    for path in file_paths:
        if path.endswith(f"{module}.py"):
            return path
        if path.split("/")[-1].split(".")[0] == module:
            return path
    return ""

def get_imports_for_file(file: str, imports_by_file: Dict[str, List[Dict]]) -> Set[str]:
    """Get all modules imported by a file"""
    imported = set()
    for imp in imports_by_file.get(file, []):
        if imp["type"] == "importfrom":
            imported.add(imp["module"])
    return imported

def analyze_codebase_with_llm(asts: Dict[str, Any], graph: nx.DiGraph):
    """Analyze the codebase structure using an LLM"""
    # Extract file structures and relationships for the prompt
    file_structures = {}
    for file, ast_dict in asts.items():
        # Extract abstractions
        abstractions = []
        extract_abstractions(ast_dict, {file: abstractions}, file)
        
        # Extract imports
        imports = extract_imports(ast_dict)
        
        # Extract function calls
        calls = extract_function_calls(ast_dict)
        
        # Extract simplified AST (top-level nodes only)
        simplified_ast = simplify_ast(ast_dict)
        
        file_structures[file] = {
            "abstractions": abstractions,
            "imports": imports,
            "calls": calls,
            "simplified_ast": simplified_ast
        }
    
    # Create dependency information from graph
    dependencies = []
    for u, v, data in graph.edges(data=True):
        if data.get('type') in ('imports_from', 'calls'):
            dependencies.append(f"{u} -> {v} ({data.get('type')})")
    
    # Create the prompt
    prompt = """You are analyzing a Python codebase. I'll provide the structure of each file, including simplified AST representations, and their relationships.
Please analyze this information and provide:

1. A high-level overview of the codebase's architecture
2. The main components and their responsibilities
3. The relationships and dependencies between files
4. Any design patterns you can identify
5. Suggestions for improving the architecture (if any)

Here's the codebase structure:

"""
    
    # Add file details to prompt
    for file, structure in file_structures.items():
        prompt += f"\n## File: {file}\n"
        
        if structure["imports"]:
            prompt += "\nImports:\n"
            for imp in structure["imports"]:
                if imp["type"] == "importfrom":
                    prompt += f"- from {imp['module']} import {imp['name']}"
                    if imp["alias"]:
                        prompt += f" as {imp['alias']}"
                    prompt += "\n"
                else:
                    prompt += f"- import {imp['module']}"
                    if imp["alias"]:
                        prompt += f" as {imp['alias']}"
                    prompt += "\n"
        
        if structure["abstractions"]:
            prompt += "\nDefinitions:\n"
            for item in structure["abstractions"]:
                prompt += f"- {item['type'].capitalize()}: {item['name']} (line {item['lineno']})\n"
        
        if structure["calls"]:
            prompt += "\nFunction calls:\n"
            for call in structure["calls"]:
                if call["type"] == "call":
                    prompt += f"- Calls: {call['name']}() (line {call['lineno']})\n"
                else:
                    prompt += f"- Method call: {call['object']}.{call['method']}() (line {call['lineno']})\n"
        
        # Add simplified AST information
        prompt += "\nSimplified AST structure:\n```\n"
        prompt += json.dumps(structure["simplified_ast"], indent=2)[:1500]  # Limit size
        if len(json.dumps(structure["simplified_ast"], indent=2)) > 1500:
            prompt += "...(truncated)"
        prompt += "\n```\n"
    
    # Add relationship information
    prompt += "\n## Relationships between files:\n"
    for dep in dependencies[:50]:  # Limit to avoid token limits
        prompt += f"- {dep}\n"
    
    # Configure Gemini API
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    try:
        response = model.generate_content(prompt)
        return response.text if response else "[No response from LLM]"
    except Exception as e:
        return f"Error analyzing codebase: {str(e)}"

def simplify_ast(ast_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Create a simplified version of an AST for LLM analysis"""
    if not isinstance(ast_dict, dict):
        return {"simplified": "non-dict value"}
    
    # For the module (top level)
    if ast_dict.get("_type") == "Module":
        simplified = {
            "_type": "Module",
            "body": []
        }
        
        # Process top-level statements
        for item in ast_dict.get("body", []):
            if isinstance(item, dict):
                node_type = item.get("_type")
                
                if node_type == "ImportFrom" or node_type == "Import":
                    # Already covered in imports section
                    simplified["body"].append({
                        "_type": node_type,
                        "module": item.get("module"),
                        "names": [name.get("name") for name in item.get("names", [])]
                    })
                
                elif node_type == "ClassDef":
                    # Simplify class definition
                    class_info = {
                        "_type": "ClassDef",
                        "name": item.get("name"),
                        "bases": [get_name_from_node(base) for base in item.get("bases", [])],
                        "methods": []
                    }
                    
                    # Extract method names
                    for method in item.get("body", []):
                        if isinstance(method, dict) and method.get("_type") == "FunctionDef":
                            class_info["methods"].append(method.get("name"))
                    
                    simplified["body"].append(class_info)
                
                elif node_type == "FunctionDef":
                    # Simplify function definition
                    func_info = {
                        "_type": "FunctionDef",
                        "name": item.get("name"),
                        "args": extract_arg_names(item.get("args", {})),
                        "body_summary": summarize_body(item.get("body", []))
                    }
                    simplified["body"].append(func_info)
                
                else:
                    # Other top-level items
                    simplified["body"].append({
                        "_type": node_type,
                        "summary": f"{node_type} at line {item.get('lineno')}"
                    })
        
        return simplified
    
    # For other node types, just return type and basic info
    return {
        "_type": ast_dict.get("_type"),
        "summary": f"{ast_dict.get('_type')} node (simplified)"
    }

def get_name_from_node(node: Dict[str, Any]) -> str:
    """Extract a name from a node (for bases in class definitions)"""
    if not isinstance(node, dict):
        return "unknown"
    
    if node.get("_type") == "Name":
        return node.get("id", "unknown")
    elif node.get("_type") == "Attribute":
        return f"{get_name_from_node(node.get('value'))}.{node.get('attr', 'unknown')}"
    
    return "complex_expr"

def extract_arg_names(args_node: Dict[str, Any]) -> List[str]:
    """Extract argument names from a function definition"""
    if not isinstance(args_node, dict):
        return []
    
    arg_names = []
    
    # Regular arguments
    for arg in args_node.get("args", []):
        if isinstance(arg, dict):
            arg_names.append(arg.get("arg", "unknown"))
    
    # Keyword-only arguments
    for arg in args_node.get("kwonlyargs", []):
        if isinstance(arg, dict):
            arg_names.append(arg.get("arg", "unknown"))
    
    # *args
    if args_node.get("vararg") and isinstance(args_node["vararg"], dict):
        arg_names.append(f"*{args_node['vararg'].get('arg', 'args')}")
    
    # **kwargs
    if args_node.get("kwarg") and isinstance(args_node["kwarg"], dict):
        arg_names.append(f"**{args_node['kwarg'].get('arg', 'kwargs')}")
    
    return arg_names

def summarize_body(body_nodes: List[Dict[str, Any]]) -> List[str]:
    """Provide a brief summary of function body contents"""
    summary = []
    
    for node in body_nodes[:5]:  # Limit to first 5 statements
        if not isinstance(node, dict):
            continue
            
        node_type = node.get("_type")
        
        if node_type == "Assign":
            # Assignment statement
            target_info = get_target_info(node.get("targets", []))
            summary.append(f"Assignment to {target_info}")
        
        elif node_type == "Return":
            # Return statement
            summary.append("Return statement")
        
        elif node_type == "If":
            # If statement
            summary.append("Conditional (if statement)")
        
        elif node_type == "For":
            # For loop
            summary.append("For loop")
        
        elif node_type == "While":
            # While loop
            summary.append("While loop")
        
        elif node_type == "Expr":
            # Expression statement
            expr = node.get("value", {})
            if isinstance(expr, dict) and expr.get("_type") == "Call":
                summary.append(f"Call to {get_call_target(expr)}")
            else:
                summary.append("Expression statement")
        
        else:
            summary.append(f"{node_type} statement")
    
    if len(body_nodes) > 5:
        summary.append(f"... ({len(body_nodes) - 5} more statements)")
    
    return summary

def get_target_info(targets: List[Dict[str, Any]]) -> str:
    """Get a description of assignment targets"""
    if not targets:
        return "unknown"
    
    target_names = []
    for target in targets:
        if isinstance(target, dict):
            if target.get("_type") == "Name":
                target_names.append(target.get("id", "unknown"))
            elif target.get("_type") == "Attribute":
                obj = get_object_name(target.get("value"))
                attr = target.get("attr", "unknown")
                target_names.append(f"{obj}.{attr}")
            else:
                target_names.append(f"{target.get('_type', 'unknown')}")
    
    return ", ".join(target_names)

def get_call_target(call_node: Dict[str, Any]) -> str:
    """Get the target of a function call"""
    func = call_node.get("func", {})
    if isinstance(func, dict):
        if func.get("_type") == "Name":
            return func.get("id", "unknown")
        elif func.get("_type") == "Attribute":
            obj = get_object_name(func.get("value"))
            method = func.get("attr", "unknown")
            return f"{obj}.{method}"
    
    return "unknown function"

def get_object_name(node):
    if not node:
        return "unknown"
    if not isinstance(node, dict):
        return "unknown"
    if node.get("_type") == "Name":
        return node.get("id", "unknown")
    return "complex_expr"

# Main pipeline
def main():
    base = Path("./artifacts/say_hello-ast")
    index_path = base / "index.jsonl"

    # Load ASTs
    print("Loading ASTs...")
    asts = load_asts(index_path)
    print(f"Loaded {len(asts)} AST files")
    
    # Build codebase graph
    print("Building codebase graph...")
    G = build_codebase_graph(asts)
    print(f"Graph built with {len(G.nodes)} nodes and {len(G.edges)} edges")
    
    # Analyze with LLM
    print("Analyzing codebase with LLM...")
    analysis = analyze_codebase_with_llm(asts, G)
    
    print("\n=== Codebase Analysis ===")
    print(analysis)
    
    # Save the analysis to a file
    output_dir = Path("./analysis")
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "codebase_analysis.md", "w") as f:
        f.write("# Codebase Analysis\n\n")
        f.write(analysis)
    
    print(f"\nAnalysis saved to {output_dir / 'codebase_analysis.md'}")

if __name__ == "__main__":
    main()
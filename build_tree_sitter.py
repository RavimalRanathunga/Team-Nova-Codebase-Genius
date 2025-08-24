import os
from tree_sitter import Language, Parser
import tree_sitter_python

# Step 1: Build the parser for Python (do this once and keep the .so file)
# Run this once: Language.build_library("build/my-languages.so", ["tree-sitter-python"])
PY_LANGUAGE = Language(tree_sitter_python.language())

parser = Parser()
parser.language = PY_LANGUAGE


def parse_code(code: str, file_path: str, codebase_modules=None) -> dict:
    """Parse code and extract classes, functions, relationships, line numbers, import types, and function calls."""
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node

    result = {
        "file": file_path,
        "imports": [],
        "classes": {},
        "functions": {},
        "function_calls": [], 
        "code": code
    }

    def get_text(node):
        return code[node.start_byte:node.end_byte]

    def get_lines(node):
        return (node.start_point[0] + 1, node.end_point[0] + 1)

    def classify_import(import_text):
        # Simple heuristic: check if import is from codebase modules
        if codebase_modules:
            for mod in codebase_modules:
                if import_text.startswith(f"import {mod}") or import_text.startswith(f"from {mod}"):
                    return "internal"
        # You can add more logic for standard library or third-party detection
        return "external"

    def walk(node, parent_class=None):
        if node.type == "import_statement":
            import_text = get_text(node)
            import_type = classify_import(import_text)
            result["imports"].append({
                "text": import_text,
                "lines": get_lines(node),
                "type": import_type
            })

        elif node.type == "class_definition":
            class_name = get_text(node.child_by_field_name("name"))
            start_line, end_line = get_lines(node)
            result["classes"][class_name] = {
                "methods": {},
                "inherits": [],
                "lines": (start_line, end_line)
            }
            bases = node.child_by_field_name("superclasses")
            if bases:
                result["classes"][class_name]["inherits"] = [
                    get_text(c) for c in bases.children if c.type == "identifier"
                ]
            for child in node.children:
                walk(child, parent_class=class_name)

        elif node.type == "function_definition":
            func_name = get_text(node.child_by_field_name("name"))
            params = node.child_by_field_name("parameters")
            start_line, end_line = get_lines(node)
            param_list = []
            if params:
                for p in params.children:
                    if p.type == "identifier":
                        param_list.append(get_text(p))
            func_info = {
                "params": param_list,
                "lines": (start_line, end_line)
            }
            if parent_class:
                result["classes"][parent_class]["methods"][func_name] = func_info
            else:
                result["functions"][func_name] = func_info

        elif node.type == "call":
            # Function call node
            func_node = node.child_by_field_name("function")
            if func_node:
                func_name = get_text(func_node)
                start_line, end_line = get_lines(node)
                result["function_calls"].append({
                    "name": func_name,
                    "lines": (start_line, end_line)
                })
            for child in node.children:
                walk(child, parent_class)

        else:
            for child in node.children:
                walk(child, parent_class)

    walk(root_node)
    return result


def traverse_and_parse(structure: dict) -> dict:
    """Traverse the folder structure and parse code files with Tree-sitter."""
    analysis = {}

    # Collect all module names in the codebase for import classification
    def collect_modules(node, modules):
        for name, child in node.items():
            if isinstance(child, dict):
                collect_modules(child, modules)
            elif isinstance(child, list) and name.endswith(".py"):
                mod_name = os.path.splitext(name)[0]
                modules.add(mod_name)
    codebase_modules = set()
    collect_modules(structure, codebase_modules)

    def recurse(node):
        for name, child in node.items():
            if isinstance(child, dict):  # folder
                recurse(child)
            elif isinstance(child, list) and name.endswith(".py"):
                with open(child[1], "r", encoding="utf-8") as f:
                    code = f.read()
                analysis[name] = parse_code(code, child[1], codebase_modules)
            else:
                continue
    recurse(structure)
    return analysis


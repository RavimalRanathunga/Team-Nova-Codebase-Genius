import ast

# Example code (you can read from a file instead)
code = """
class User:
    def __init__(self, name):
        self.name = name

    def greet(self):
        print(f"Hello, {self.name}!")

def helper_function():
    for i in range(10):
        print(i)
"""

# Parse the code to AST
tree = ast.parse(code)

def build_ast_tree(node, indent=0):
    node_name = type(node).__name__
    
    # Add extra info for classes, functions, loops, and assignments
    if isinstance(node, ast.Module):
        label = f"Module (lines: 1-{len(code.splitlines())})"
    elif isinstance(node, ast.ClassDef):
        label = f"ClassDef: {node.name} (lines: {node.lineno}-{node.end_lineno})"
    elif isinstance(node, ast.FunctionDef):
        label = f"FunctionDef: {node.name} (lines: {node.lineno}-{node.end_lineno})"
    elif isinstance(node, ast.For):
        label = f"For Loop (lines: {node.lineno}-{node.end_lineno})"
    elif isinstance(node, ast.Assign):
        targets = ", ".join([ast.unparse(t) for t in node.targets])
        label = f"Assign: {targets} = {ast.unparse(node.value)} (line: {node.lineno})"
    elif isinstance(node, ast.Expr):
        label = f"Expr: {ast.unparse(node.value)} (line: {node.lineno})"
    else:
        label = node_name
    
    # Print current node with indentation
    print(" " * indent + label)
    
    # Recursively print children
    for child in ast.iter_child_nodes(node):
        build_ast_tree(child, indent + 4)  # increase indent for children

# Print the AST tree
build_ast_tree(tree)

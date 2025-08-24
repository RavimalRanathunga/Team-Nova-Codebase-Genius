#!/usr/bin/env python3
"""
repo_ast_parser.py

Clones a target Git repository and parses all Python source files into
Abstract Syntax Trees (ASTs). Outputs machine-friendly JSON for each file
and an index file you can consume downstream.

No external Python dependencies required (uses the standard library),
but the `git` CLI must be installed and on PATH.

Example usage:
  python repo_ast_parser.py \
    --repo https://github.com/psf/requests.git \
    --dest ./repos/requests \
    --output ./artifacts/requests_ast \
    --depth 1 \
    --workers 4

Outputs:
  - One JSON per parsed .py file in <output>/files/<relative_path>.ast.json
  - An index JSONL (<output>/index.jsonl) with a line per file, containing
    file metadata and the AST location.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed

# --------------------------- Git Utilities --------------------------- #

def run(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run a shell command and return (code, stdout, stderr)."""
    proc = subprocess.Popen(
        cmd, cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    out, err = proc.communicate()
    return proc.returncode, out, err


def clone_repo(repo_url: str, dest: Path, branch: Optional[str] = None, depth: int = 1) -> None:
    """Shallow clone a git repository to dest. If dest exists, fetch and reset."""
    dest = dest.resolve()
    if dest.exists() and (dest / ".git").exists():
        # Repo exists; fetch latest
        print(f"[git] Repository exists at {dest}. Fetching updates...")
        code, out, err = run(["git", "fetch", "--all"], cwd=dest)
        if code != 0:
            raise RuntimeError(f"git fetch failed: {err}")
        if branch:
            code, out, err = run(["git", "checkout", branch], cwd=dest)
            if code != 0:
                raise RuntimeError(f"git checkout {branch} failed: {err}")
        code, out, err = run(["git", "reset", "--hard", f"origin/{branch}" if branch else "HEAD"], cwd=dest)
        if code != 0:
            raise RuntimeError(f"git reset failed: {err}")
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["git", "clone", repo_url, str(dest)]
        if depth and depth > 0:
            cmd[2:2] = ["--depth", str(depth)]
        if branch:
            cmd[2:2] = ["--branch", branch]
        print(f"[git] Cloning {repo_url} -> {dest}")
        code, out, err = run(cmd)
        if code != 0:
            raise RuntimeError(f"git clone failed: {err}")

# --------------------------- File Discovery --------------------------- #

EXCLUDE_DIRS = {".git", "__pycache__", "venv", ".venv", "env", "build", "dist", "site-packages", "node_modules"}


def iter_python_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        # prune directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                yield Path(dirpath) / fn

# --------------------------- AST Serialization --------------------------- #

# The standard ast.AST is not JSON-serializable. We'll convert nodes to
# nested dicts/lists/primitives, preserving structure and locations.

def ast_to_dict(node: Any) -> Any:
    if isinstance(node, ast.AST):
        result: Dict[str, Any] = {"_type": node.__class__.__name__}
        for field in node._fields or ():
            result[field] = ast_to_dict(getattr(node, field))
        # Include location info when available
        for attr in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
            if hasattr(node, attr):
                result[attr] = getattr(node, attr)
        return result
    elif isinstance(node, list):
        return [ast_to_dict(x) for x in node]
    elif isinstance(node, (str, int, float, type(None), bool)):
        return node
    else:
        # Fallback: string representation
        return repr(node)

# --------------------------- Parsing Logic --------------------------- #

@dataclass
class ParseResult:
    path: str
    ok: bool
    error: Optional[str]
    ast_json_path: Optional[str]
    n_nodes: Optional[int]


def count_nodes(node: ast.AST) -> int:
    count = 1
    for child in ast.iter_child_nodes(node):
        count += count_nodes(child)
    return count


def parse_and_write(file_path: Path, repo_root: Path, out_root: Path) -> ParseResult:
    rel = file_path.relative_to(repo_root)
    out_file = out_root / "files" / (str(rel) + ".ast.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(rel), type_comments=True)
        ast_dict = ast_to_dict(tree)
        out_file.write_text(json.dumps(ast_dict, ensure_ascii=False))
        return ParseResult(
            path=str(rel).replace(os.sep, "/"),
            ok=True,
            error=None,
            ast_json_path=str(out_file),
            n_nodes=count_nodes(tree),
        )
    except SyntaxError as e:
        return ParseResult(
            path=str(rel).replace(os.sep, "/"),
            ok=False,
            error=f"SyntaxError: {e}",
            ast_json_path=None,
            n_nodes=None,
        )
    except Exception as e:
        return ParseResult(
            path=str(rel).replace(os.sep, "/"),
            ok=False,
            error=f"Error: {type(e).__name__}: {e}",
            ast_json_path=None,
            n_nodes=None,
        )

# --------------------------- Main Pipeline --------------------------- #

def build(repo_url: str, dest: Path, output: Path, branch: Optional[str], depth: int, workers: int) -> None:
    clone_repo(repo_url, dest, branch=branch, depth=depth)

    py_files = list(iter_python_files(dest))
    print(f"[scan] Found {len(py_files)} Python files.")

    output.mkdir(parents=True, exist_ok=True)

    results: List[ParseResult] = []
    if workers <= 1:
        for p in py_files:
            results.append(parse_and_write(p, dest, output))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            fut_to_path = {ex.submit(parse_and_write, p, dest, output): p for p in py_files}
            for i, fut in enumerate(as_completed(fut_to_path), 1):
                res = fut.result()
                results.append(res)
                if i % 25 == 0 or i == len(py_files):
                    print(f"[parse] {i}/{len(py_files)} done...")

    # Write index JSONL
    index_path = output / "index.jsonl"
    with index_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    print(f"[done] Wrote index to {index_path}")

    # Small summary
    n_ok = sum(1 for r in results if r.ok)
    n_err = len(results) - n_ok
    total_nodes = sum(r.n_nodes or 0 for r in results)
    print(f"[summary] OK: {n_ok}, Errors: {n_err}, Total AST nodes: {total_nodes}")

# --------------------------- CLI --------------------------- #

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Clone a repo and parse Python files to AST JSON.")
    p.add_argument("--repo", required=True, help="Git repository URL")
    p.add_argument("--dest", required=True, help="Local checkout directory")
    p.add_argument("--output", required=True, help="Directory to write AST artifacts")
    p.add_argument("--branch", default=None, help="Branch or tag to checkout")
    p.add_argument("--depth", type=int, default=1, help="Shallow clone depth (0 for full)")
    p.add_argument("--workers", type=int, default=os.cpu_count() or 4, help="Parallel parse workers")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    depth = None if args.depth is None else int(args.depth)
    if depth is not None and depth <= 0:
        depth = 0  # full clone
    build(
        repo_url=args.repo,
        dest=Path(args.dest),
        output=Path(args.output),
        branch=args.branch,
        depth=depth or 0,
        workers=int(args.workers),
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted.")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

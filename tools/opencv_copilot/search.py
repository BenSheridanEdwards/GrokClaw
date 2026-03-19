#!/usr/bin/env python3
"""
Tree-sitter semantic search for GrokClaw (TS/Shell/Python).
Returns top files/chunks with scores. No external APIs/embeddings.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Lazy imports for tree-sitter (optional deps)
def _get_parser():
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
    import tree_sitter_bash as tsbash
    import tree_sitter_typescript as tstypescript

    py_lang = Language(tspython.language())
    bash_lang = Language(tsbash.language())
    ts_lang = Language(tstypescript.language_typescript())
    tsx_lang = Language(tstypescript.language_tsx())

    return {
        ".py": (Parser(py_lang), "python"),
        ".sh": (Parser(bash_lang), "bash"),
        ".ts": (Parser(ts_lang), "typescript"),
        ".tsx": (Parser(tsx_lang), "tsx"),
        ".js": (Parser(ts_lang), "javascript"),
    }


# Symbol capture queries per language (tree-sitter query syntax)
QUERIES = {
    "python": """
    (function_definition name: (identifier) @name)
    (class_definition name: (identifier) @name)
    (decorated_definition definition: (function_definition name: (identifier) @name))
    """,
    "bash": """
    (function_definition name: (word) @name)
    (command_name) @name
    """,
    "typescript": """
    (function_declaration name: (identifier) @name)
    (method_definition name: (property_identifier) @name)
    (class_declaration name: (type_identifier) @name)
    (lexical_declaration (variable_declarator name: (identifier) @name))
    """,
    "tsx": """
    (function_declaration name: (identifier) @name)
    (method_definition name: (property_identifier) @name)
    (class_declaration name: (type_identifier) @name)
    (lexical_declaration (variable_declarator name: (identifier) @name))
    """,
    "javascript": """
    (function_declaration name: (identifier) @name)
    (method_definition name: (property_identifier) @name)
    (class_declaration name: (type_identifier) @name)
    (lexical_declaration (variable_declarator name: (identifier) @name))
    """,
}


def _extract_symbols(parser_map, ext: str, source: bytes, filepath: str) -> list[tuple[str, int, int]]:
    """Extract symbol names and their byte ranges from source."""
    if ext not in parser_map:
        return []
    parser, lang = parser_map[ext]
    try:
        tree = parser.parse(source)
    except Exception:
        return []
    if not tree or not tree.root_node:
        return []

    from tree_sitter import Query, QueryCursor

    query_src = QUERIES.get(lang)
    if not query_src:
        return []
    try:
        lang_obj = parser.language
        query = Query(lang_obj, query_src)
    except Exception:
        return []

    results = []
    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)
    for node in captures.get("name", []):
        start = node.start_byte
        end = node.end_byte
        name = source[start:end].decode("utf-8", errors="replace")
        results.append((name, node.start_point[0] + 1, node.end_point[0] + 1))
    return results


def _score_match(query_lower: str, text: str) -> float:
    """Score how well text matches the query. Higher = better."""
    if not query_lower or not text:
        return 0.0
    text_lower = text.lower()
    score = 0.0
    # Exact phrase match
    if query_lower in text_lower:
        score += 2.0
    # Word-by-word
    words = re.findall(r"\w+", query_lower)
    for w in words:
        if len(w) < 2:
            continue
        if w in text_lower:
            score += 1.0
        elif any(w in t for t in text_lower.split()):
            score += 0.5
    return score


def _get_snippet(lines: list[str], line_no: int, context: int = 3) -> str:
    """Get a code snippet around line_no."""
    start = max(0, line_no - 1 - context)
    end = min(len(lines), line_no + context)
    return "\n".join(lines[start:end])


def search(
    workspace_root: str,
    query: str,
    *,
    limit: int = 10,
    extensions: tuple[str, ...] = (".py", ".sh", ".ts", ".tsx", ".js"),
    exclude_dirs: tuple[str, ...] = (".git", "node_modules", "__pycache__", ".venv", "venv"),
) -> list[dict]:
    """
    Search workspace for query. Returns list of {path, score, line, name, snippet}.
    """
    root = Path(workspace_root)
    if not root.is_dir():
        return []

    try:
        parser_map = _get_parser()
    except ImportError as e:
        raise RuntimeError(
            "opencv-copilot requires tree-sitter. Install: pip install -r requirements-opencv-copilot.txt"
        ) from e

    query_lower = query.lower().strip()
    if not query_lower:
        return []

    scored: list[tuple[float, str, int, str, str]] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in extensions:
            continue
        if any(ex in path.parts for ex in exclude_dirs):
            continue

        try:
            raw = path.read_bytes()
        except (OSError, UnicodeDecodeError):
            continue
        try:
            source = raw.decode("utf-8", errors="replace")
        except Exception:
            continue

        rel = str(path.relative_to(root))
        symbols = _extract_symbols(parser_map, path.suffix, raw, rel)
        lines = source.splitlines()

        for name, line_start, line_end in symbols:
            score = _score_match(query_lower, name)
            if score <= 0:
                continue
            snippet = _get_snippet(lines, line_start)
            scored.append((score, rel, line_start, name, snippet))

    scored.sort(key=lambda x: (-x[0], x[1], x[2]))
    seen = set()
    out = []
    for score, rel, line, name, snippet in scored[: limit * 3]:
        key = (rel, line)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "path": rel,
            "score": round(score, 2),
            "line": line,
            "name": name,
            "snippet": snippet,
        })
        if len(out) >= limit:
            break
    return out


def main_search(argv: list[str], workspace_root: str) -> int:
    """CLI entry for search subcommand."""
    if len(argv) < 2:
        print("usage: opencv-copilot search <query> [--limit N]", file=sys.stderr)
        return 1
    query = argv[1]
    limit = 10
    if "--limit" in argv:
        idx = argv.index("--limit")
        if idx + 1 < len(argv):
            try:
                limit = int(argv[idx + 1])
            except ValueError:
                pass

    try:
        results = search(workspace_root, query, limit=limit)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    for r in results:
        print(f"{r['path']}:{r['line']} (score={r['score']}) {r['name']}")
        print(f"  ---")
        for line in r["snippet"].splitlines():
            print(f"  {line}")
        print()
    return 0

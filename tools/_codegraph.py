#!/usr/bin/env python3
"""
Code Graph Visualizer — parse JS/TS/Python/Rust codebases into a graph.

Extracts:
  - Nodes: files, functions
  - Edges: imports, function calls
  - Token counts per file (tiktoken)
  - Interactive HTML (D3), JSON export for LLMs, PNG/SVG/PDF export

Usage:
  python3 _codegraph.py /path/to/repo [--output graph.html] [--format json|html|all]
  codegraph /path/to/repo --output graph.html

Requires: pip install tree-sitter tree-sitter-language-pack tiktoken
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import tiktoken
except ImportError:
    tiktoken = None

try:
    import tree_sitter
    from tree_sitter_language_pack import get_language, get_parser
except ImportError:
    tree_sitter = None
    get_language = get_parser = None


# Map file extensions to tree-sitter language names
LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".rs": "rust",
}


def get_lang_for_path(path: str) -> str | None:
    suffix = Path(path).suffix.lower()
    return LANG_MAP.get(suffix)


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken (cl100k_base, GPT-4 style)."""
    if not tiktoken:
        return len(text.split())  # fallback: word count
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return len(text.split())


def collect_source_files(root: Path, exts: set[str]) -> list[Path]:
    """Yield source file paths under root, respecting .gitignore patterns."""
    ignore_dirs = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}
    files = []
    for p in root.rglob("*"):
        if p.is_dir() and p.name in ignore_dirs:
            continue
        if p.is_file() and p.suffix.lower() in exts:
            try:
                p.relative_to(root)
            except ValueError:
                continue
            files.append(p)
    return sorted(files)


def parse_python(tree: tree_sitter.Tree, src: bytes, filepath: str) -> tuple[list[dict], list[dict]]:
    """Extract nodes and edges from Python AST."""
    nodes = []
    edges = []
    root = tree.root_node

    def get_text(n: tree_sitter.Node) -> str:
        return src[n.start_byte:n.end_byte].decode("utf-8", errors="replace")

    # Import edges: from X import Y / import X
    for node in _iter_children(root):
        if node.type == "import_statement":
            # import foo, bar
            for name in node.children:
                if name.type == "dotted_name":
                    mod = get_text(name)
                    edges.append({"from": filepath, "to": mod, "type": "import"})
        elif node.type == "import_from_statement":
            module = None
            for child in node.children:
                if child.type == "dotted_name":
                    module = get_text(child)
                    break
            if module:
                edges.append({"from": filepath, "to": module, "type": "import"})

    # Function definitions
    for node in _walk_tree(root):
        if node.type == "function_definition":
            name_node = _first_child(node, "identifier")
            if name_node:
                name = get_text(name_node)
                nodes.append({"id": f"{filepath}::{name}", "file": filepath, "name": name, "kind": "function"})

    return nodes, edges


def parse_javascript(tree: tree_sitter.Tree, src: bytes, filepath: str) -> tuple[list[dict], list[dict]]:
    """Extract nodes and edges from JavaScript/TypeScript AST."""
    nodes = []
    edges = []
    root = tree.root_node

    def get_text(n: tree_sitter.Node) -> str:
        return src[n.start_byte:n.end_byte].decode("utf-8", errors="replace")

    for node in _walk_tree(root):
        if node.type == "import_statement":
            src_node = _first_descendant(node, "string")
            if src_node:
                imp = get_text(src_node).strip("'\"")
                edges.append({"from": filepath, "to": imp, "type": "import"})
        elif node.type in ("lexical_declaration", "variable_declaration"):
            for child in node.children:
                if child.type == "call_expression":
                    callee = _first_child(child, "identifier") or _first_child(child, "member_expression")
                    if callee and _get_call_name(callee, src) == "require":
                        arg = _first_descendant(child, "string")
                        if arg:
                            imp = get_text(arg).strip("'\"")
                            edges.append({"from": filepath, "to": imp, "type": "import"})
        elif node.type in ("function_declaration", "method_definition"):
            name_node = _first_child(node, "identifier") or _first_child(node, "property_identifier")
            if name_node:
                name = get_text(name_node)
                nodes.append({"id": f"{filepath}::{name}", "file": filepath, "name": name, "kind": "function"})

    return nodes, edges


def _get_call_name(node: tree_sitter.Node, src: bytes) -> str:
    if node.type == "identifier":
        return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
    if node.type == "member_expression":
        obj = _first_child(node, "identifier") or _first_child(node, "member_expression")
        prop = _first_child(node, "property_identifier")
        if obj and prop:
            return src[prop.start_byte:prop.end_byte].decode("utf-8", errors="replace")
    return ""


def parse_rust(tree: tree_sitter.Tree, src: bytes, filepath: str) -> tuple[list[dict], list[dict]]:
    """Extract nodes and edges from Rust AST."""
    nodes = []
    edges = []
    root = tree.root_node

    def get_text(n: tree_sitter.Node) -> str:
        return src[n.start_byte:n.end_byte].decode("utf-8", errors="replace")

    for node in _walk_tree(root):
        if node.type == "use_declaration":
            path = _first_child(node, "scoped_identifier") or _first_child(node, "identifier")
            if path:
                full = get_text(path)
                edges.append({"from": filepath, "to": full, "type": "import"})
        elif node.type == "function_item":
            name_node = _first_child(node, "identifier")
            if name_node:
                name = get_text(name_node)
                nodes.append({"id": f"{filepath}::{name}", "file": filepath, "name": name, "kind": "function"})

    return nodes, edges


def _first_child(node: tree_sitter.Node, typ: str) -> tree_sitter.Node | None:
    for c in node.children:
        if c.type == typ:
            return c
    return None


def _first_descendant(node: tree_sitter.Node, typ: str) -> tree_sitter.Node | None:
    for n in _walk_tree(node):
        if n.type == typ:
            return n
    return None


def _iter_children(node: tree_sitter.Node):
    for c in node.children:
        yield c


def _walk_tree(node: tree_sitter.Node):
    yield node
    for c in node.children:
        yield from _walk_tree(c)


def resolve_import_to_file(imp: str, from_file: str, root: Path) -> str | None:
    """Resolve import string to a file path (best-effort)."""
    imp_clean = imp.replace(".", "/")
    base_dir = (root / from_file).parent
    candidates = [
        root / imp_clean.lstrip("/"),
        root / (imp_clean + ".py"),
        root / (imp_clean + ".ts"),
        root / (imp_clean + ".tsx"),
        root / (imp_clean + ".js"),
        root / (imp_clean + ".jsx"),
        root / (imp_clean + "/__init__.py"),
        root / (imp_clean + "/index.ts"),
        root / (imp_clean + "/index.js"),
        base_dir / imp_clean,
        base_dir / (imp_clean + ".py"),
        base_dir / (imp_clean + ".ts"),
        base_dir / (imp_clean + ".js"),
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            try:
                return str(c.relative_to(root))
            except ValueError:
                pass
    return None


def build_graph(repo_path: Path) -> dict:
    """Parse repo and build graph: nodes, edges, token counts."""
    if not tree_sitter or not get_parser:
        sys.stderr.write("Install: pip install tree-sitter tree-sitter-language-pack\n")
        sys.exit(1)

    root = repo_path.resolve()
    exts = set(LANG_MAP.keys())
    files = collect_source_files(root, exts)

    all_nodes = []
    all_edges = []
    file_tokens = {}
    parsers = {}

    for fp in files:
        rel = str(fp.relative_to(root))
        lang = get_lang_for_path(rel)
        if not lang:
            continue
        try:
            src_bytes = fp.read_bytes()
        except OSError:
            continue
        src_str = src_bytes.decode("utf-8", errors="replace")

        file_tokens[rel] = count_tokens(src_str)

        if lang not in parsers:
            try:
                parsers[lang] = get_parser(lang)
            except Exception:
                continue

        parser = parsers[lang]
        tree = parser.parse(src_bytes)

        if lang == "python":
            nodes, edges = parse_python(tree, src_bytes, rel)
        elif lang in ("javascript", "typescript", "tsx"):
            nodes, edges = parse_javascript(tree, src_bytes, rel)
        elif lang == "rust":
            nodes, edges = parse_rust(tree, src_bytes, rel)
        else:
            nodes, edges = [], []

        all_nodes.extend(nodes)

        for e in edges:
            to_path = resolve_import_to_file(e["to"], e["from"], root)
            if to_path and to_path != e["from"]:
                e["to"] = to_path
                all_edges.append(e)
            elif not to_path and "/" not in e["to"] and ":" not in e["to"]:
                all_edges.append(e)

    file_nodes = [
        {"id": f, "file": f, "name": Path(f).name, "kind": "file", "tokens": file_tokens.get(f, 0)}
        for f in file_tokens
    ]

    nodes_by_id = {n["id"]: n for n in all_nodes}
    for fn in file_nodes:
        nodes_by_id[fn["id"]] = fn

    total_tokens = sum(file_tokens.values())
    avg_tokens = total_tokens / len(file_tokens) if file_tokens else 0

    return {
        "nodes": file_nodes + all_nodes,
        "edges": all_edges,
        "stats": {
            "files": len(file_tokens),
            "total_tokens": total_tokens,
            "avg_tokens_per_file": round(avg_tokens, 1),
        },
    }


def render_html(graph: dict, output_path: Path) -> None:
    """Generate interactive D3-based HTML."""
    data_json = json.dumps(graph)
    html = _HTML_TEMPLATE.replace("__DATA_JSON__", data_json)
    output_path.write_text(html, encoding="utf-8")


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Code Graph</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    body { margin: 0; font-family: system-ui, sans-serif; background: #0d1117; color: #c9d1d9; }
    #graph { width: 100vw; height: 100vh; }
    .node { cursor: pointer; }
    .node circle { stroke: #58a6ff; stroke-width: 1.5; }
    .node:hover circle { stroke: #79c0ff; stroke-width: 2; }
    .link { stroke: #30363d; stroke-opacity: 0.8; }
    .link:hover { stroke: #58a6ff; stroke-opacity: 1; }
    #controls { position: fixed; top: 10px; left: 10px; background: #161b22; padding: 12px; border-radius: 8px; font-size: 12px; }
    #controls input { margin: 4px; }
    #stats { position: fixed; bottom: 10px; left: 10px; font-size: 11px; opacity: 0.8; }
  </style>
</head>
<body>
  <div id="controls">
    <input type="text" id="search" placeholder="Search nodes..." />
    <label><input type="checkbox" id="fileOnly" /> Files only</label>
    <button id="center">Center</button>
    <button id="exportSvg">Export SVG</button>
    <button id="exportPng">Export PNG</button>
  </div>
  <div id="stats"></div>
  <div id="graph"></div>
  <script>
    const graph = __DATA_JSON__;
    const files = graph.nodes.filter(n => n.kind === "file");
    const links = graph.edges.map(e => ({
      source: e.from,
      target: e.to,
      type: e.type || "import"
    }));

    const width = window.innerWidth;
    const height = window.innerHeight;
    const svg = d3.select("#graph").append("svg").attr("width", width).attr("height", height);
    const g = svg.append("g");

    const zoom = d3.zoom().scaleExtent([0.1, 4]).on("zoom", (e) => g.attr("transform", e.transform));
    svg.call(zoom);

    const simulation = d3.forceSimulation(files.map(f => ({ ...f, id: f.id })))
      .force("link", d3.forceLink(links).id(d => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width/2, height/2));

    const link = g.append("g").selectAll("line")
      .data(links)
      .join("line")
      .attr("class", "link")
      .attr("stroke-width", 1);

    const node = g.append("g").selectAll("g")
      .data(files)
      .join("g")
      .attr("class", "node")
      .call(d3.drag()
        .on("start", (e, d) => { e.sourceEvent.stopPropagation(); simulation.alpha(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end", (e, d) => { d.fx = null; d.fy = null; }));

    node.append("circle").attr("r", d => 4 + Math.min(d.tokens / 500, 12));
    node.append("text").attr("dx", 8).attr("dy", 4).text(d => d.name).attr("font-size", 10);

    simulation.on("tick", () => {
      link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    document.getElementById("search").oninput = (e) => {
      const q = (e.target.value || "").toLowerCase();
      node.style("opacity", d => !q || d.name.toLowerCase().includes(q) ? 1 : 0.2);
    };
    document.getElementById("center").onclick = () => {
      svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity.translate(width/2 - 200, height/2 - 100).scale(0.8));
    };
    document.getElementById("exportSvg").onclick = () => {
      const blob = new Blob([document.getElementById("graph").innerHTML], { type: "image/svg+xml" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "codegraph.svg";
      a.click();
    };
    document.getElementById("exportPng").onclick = () => {
      const svgEl = document.querySelector("#graph svg");
      if (!svgEl) return;
      const canvas = document.createElement("canvas");
      const rect = svgEl.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      const ctx = canvas.getContext("2d");
      const img = new Image();
      const svgBlob = new Blob([new XMLSerializer().serializeToString(svgEl)], { type: "image/svg+xml;charset=utf-8" });
      img.onload = () => {
        ctx.drawImage(img, 0, 0);
        canvas.toBlob(blob => {
          const a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = "codegraph.png";
          a.click();
        });
      };
      img.src = URL.createObjectURL(svgBlob);
    };

    document.getElementById("stats").textContent = `Files: ${graph.stats.files} | Tokens: ${graph.stats.total_tokens.toLocaleString()} | Avg: ${graph.stats.avg_tokens_per_file}`;
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Code Graph Visualizer")
    parser.add_argument("path", type=str, nargs="?", default=".", help="Repo path")
    parser.add_argument("--output", "-o", type=str, default="graph.html", help="Output path")
    parser.add_argument("--format", "-f", choices=["html", "json", "all"], default="all",
                        help="Output format")
    args = parser.parse_args()

    repo_path = Path(args.path).resolve()
    if not repo_path.is_dir():
        sys.stderr.write(f"Not a directory: {repo_path}\n")
        return 1

    graph = build_graph(repo_path)
    out_path = Path(args.output).resolve()

    if args.format in ("html", "all"):
        if out_path.suffix != ".html" and args.format == "all":
            out_path = out_path / "graph.html" if out_path.is_dir() else out_path.with_suffix(".html")
        render_html(graph, out_path)
        print(f"HTML: {out_path}")

    if args.format in ("json", "all"):
        json_path = out_path.with_suffix(".json") if out_path.suffix == ".html" else out_path.parent / "graph.json"
        json_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
        print(f"JSON: {json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

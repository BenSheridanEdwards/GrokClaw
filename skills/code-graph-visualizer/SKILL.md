---
name: code-graph-visualizer
description: Visualize codebases as graphs for LLM analysis. Use when the user wants to visualize a codebase as a graph, see dependencies/imports/call structure, estimate token counts per file, or export a graph for Claude/LLM context.
---

# Code Graph Visualizer

Parse JS/TS/Python/Rust codebases into nodes (files, functions) and edges (imports, calls). Output interactive D3 graph, JSON for LLMs, and SVG/PNG export.

## When to use

- User asks to visualize a codebase as a graph
- Need to understand dependency structure before analysis
- Token estimation per file for context budgeting
- Export graph for LLM context (JSON) or sharing (HTML, SVG, PNG)

## Quick start

```bash
./tools/codegraph.sh /path/to/repo --output graph.html
```

Output: `graph.html` (interactive), `graph.json` (LLM-friendly).

## Requirements

```bash
pip install -r tools/requirements-codegraph.txt
```

## Workflow

1. Run from workspace root: `./tools/codegraph.sh <path> -o graph.html`
2. Open `graph.html` in a browser for interactive zoom/pan, search, export
3. Use `graph.json` for LLM context — includes nodes, edges, token counts

## OpenClaw integration

- **Canvas tool**: Not available in OpenClaw. Use browser to open the generated HTML.
- **Browser tool**: `browser(action="snapshot", url="file:///path/to/graph.html")` if HTML is served, or open locally.
- **Read/edit**: Agent can run codegraph, then read graph.json for structured context.

## Output formats

| Format | Use |
|--------|-----|
| HTML | Interactive D3 viz: zoom, search, Export SVG/PNG |
| JSON | LLM context: nodes, edges, stats (files, total/avg tokens) |
| SVG | Export from UI button — vector, scalable |
| PNG | Export from UI button — raster screenshot |
| PDF | Browser Print → Save as PDF |

## References

- `references/usage.md` — CLI options, filters, Graphviz fallback

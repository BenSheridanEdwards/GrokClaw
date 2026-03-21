# Code Graph Visualizer (GRO-31)

Visualize JS/TS/Python/Rust codebases as interactive dependency graphs for LLM analysis.

## Features

- **Parse**: Tree-sitter extracts nodes (files, functions) and edges (imports, calls)
- **Token estimator**: tiktoken counts tokens per file (total/avg)
- **Interactive UI**: D3 zoomable graph, search, color by token count
- **Export**: PNG, SVG via UI; JSON for LLMs; PDF via browser Print
- **CLI**: `codegraph.sh /path/to/repo --output graph.html`

## Usage

```bash
# Install deps (once)
pip install -r tools/requirements-codegraph.txt

# Generate graph
./tools/codegraph.sh . --output graph.html

# JSON only
./tools/codegraph.sh . -o graph.json -f json
```

## OpenClaw integration

- **Browser tool**: Open generated HTML locally or via `file://`; use Export SVG/PNG
- **Canvas**: Not integrated; graph is standalone HTML
- **Skill**: `skills/code-graph-visualizer/SKILL.md` — when to use, workflow

## Output

- `graph.html` — interactive D3 viz (zoom, pan, search, Export SVG/PNG)
- `graph.json` — nodes, edges, stats for LLM context

## Test on GrokClaw

```bash
./tools/codegraph.sh /path/to/GrokClaw --output /tmp/grokclaw-graph.html
```

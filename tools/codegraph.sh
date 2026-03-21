#!/bin/sh
# Code Graph Visualizer — parse JS/TS/Python/Rust and output interactive graph.
#
# Usage:
#   codegraph.sh [path] [--output graph.html]
#   codegraph.sh /path/to/repo --output graph.html
#
# Output: graph.html (interactive D3 viz), graph.json (for LLMs).
# Requires: pip install -r tools/requirements-codegraph.txt
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
# Pass through: path (default .) and any --output etc.
exec python3 "$SCRIPT_DIR/_codegraph.py" "$@"

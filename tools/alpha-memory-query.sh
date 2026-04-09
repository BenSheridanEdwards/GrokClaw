#!/bin/sh
# Query Alpha memory (MemPalace backend).
# Usage:
#   alpha-memory-query.sh query "<natural language question>"
#   alpha-memory-query.sh recent-trades
#   alpha-memory-query.sh whale-accuracy
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec python3 "$SCRIPT_DIR/alpha-memory.py" "$@"

#!/bin/sh
# Query Memvid alpha-polymarket memory.
# Usage:
#   memvid-alpha-query.sh query "<natural language question>"
#   memvid-alpha-query.sh recent-trades
#   memvid-alpha-query.sh whale-accuracy
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec python3 "$SCRIPT_DIR/memvid-alpha.py" "$@"

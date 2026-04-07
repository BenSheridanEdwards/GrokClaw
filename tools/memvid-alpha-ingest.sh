#!/bin/sh
# Ingest a Polymarket decision or result into Memvid alpha memory.
# Usage:
#   memvid-alpha-ingest.sh decision <decision.json>
#   memvid-alpha-ingest.sh result <result.json>
#   memvid-alpha-ingest.sh history
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec python3 "$SCRIPT_DIR/memvid-alpha.py" "$@"

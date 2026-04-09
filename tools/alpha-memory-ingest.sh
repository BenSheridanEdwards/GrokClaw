#!/bin/sh
# Ingest Polymarket decisions/results into Alpha memory backend.
# Usage:
#   alpha-memory-ingest.sh ingest-decision <decision.json>
#   alpha-memory-ingest.sh ingest-decision --latest
#   alpha-memory-ingest.sh ingest-result <result.json>
#   alpha-memory-ingest.sh ingest-result --latest
#   alpha-memory-ingest.sh ingest-history
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec python3 "$SCRIPT_DIR/alpha-memory.py" "$@"

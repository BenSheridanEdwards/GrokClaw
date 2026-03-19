#!/bin/sh
# Polymarket resolve: check unresolved trades against API, mark resolved, append results.
# Usage: polymarket-resolve.sh
# Run via cron (agent_turn) daily at 23:45 UTC.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec python3 "$SCRIPT_DIR/_polymarket_resolve.py" "$WORKSPACE_ROOT"

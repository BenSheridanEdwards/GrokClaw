#!/bin/sh
# Polymarket resolve: check unresolved trades against API, mark resolved, append results.
# Usage: polymarket-resolve.sh
# Run via cron (agent_turn) daily at 23:45 UTC.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

python3 "$SCRIPT_DIR/_polymarket_resolve.py" "$WORKSPACE_ROOT"
# Void stale trades (endDate+48h with no decisive price) so stuck paper
# positions stop blocking the exposure cap.
python3 "$SCRIPT_DIR/_polymarket_stale_voider.py" "$WORKSPACE_ROOT" 48
# Stop-loss: close trades where the market has moved 30pp+ against entry.
exec python3 "$SCRIPT_DIR/_polymarket_stop_loss.py" "$WORKSPACE_ROOT" 0.30

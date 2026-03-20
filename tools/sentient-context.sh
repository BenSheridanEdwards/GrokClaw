#!/bin/sh
# Load recent Sentient decisions and results for agent calibration.
# Usage: sentient-context.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

echo "=== Sentient Model Arena Context ==="
echo ""
echo "Recent report:"
"$SCRIPT_DIR/sentient-report.sh" 2>/dev/null || echo "No trades yet."
echo ""
echo "Last 5 decisions (data/sentient-decisions.json):"
tail -5 "$WORKSPACE_ROOT/data/sentient-decisions.json" 2>/dev/null || echo "None."
echo ""
echo "Last 5 results (data/sentient-results.json):"
tail -5 "$WORKSPACE_ROOT/data/sentient-results.json" 2>/dev/null || echo "None."

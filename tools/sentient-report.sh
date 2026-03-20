#!/bin/sh
# Print Sentient model-arena performance summary.
# Usage: sentient-report.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec python3 - "$WORKSPACE_ROOT" <<'PY'
import json
import sys

workspace_root = sys.argv[1]
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from tools import _sentient_metrics as metrics

summary = metrics.summarize(workspace_root)
out = {
    "current_bankroll": summary["current_bankroll"],
    "resolved_count": summary["resolved_count"],
    "wins": summary["wins"],
    "accuracy": round(summary["accuracy"] * 100, 1) if summary["resolved_count"] else 0,
    "total_pnl": summary["total_pnl"],
    "skip_count": summary["skip_count"],
}
print(json.dumps(out))
PY

#!/bin/sh
# Print Polymarket performance summary and promotion gate status.
# Usage: polymarket-report.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${PICOCLAW_WORKSPACE:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec python3 - "$WORKSPACE_ROOT" <<'PY'
import json
import os
import sys

workspace_root = sys.argv[1]
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from tools import _polymarket_metrics as metrics

summary = metrics.summarize(workspace_root)
promotion = metrics.check_promotion_gate(summary)

payload = {
    "bankroll": round(summary["current_bankroll"], 2),
    "resolved_count": summary["resolved_count"],
    "accuracy": round(summary["accuracy"], 4),
    "total_pnl": round(summary["total_pnl"], 2),
    "average_edge": None if summary["average_edge"] is None else round(summary["average_edge"], 4),
    "skip_count": summary["skip_count"],
    "brier_score": None if summary["brier_score"] is None else round(summary["brier_score"], 4),
    "max_drawdown": round(summary["max_drawdown"], 4),
    "last100_expectancy": round(summary["last100_expectancy"], 4),
    "promotion_gate": promotion,
}
print(json.dumps(payload, indent=2))
PY

#!/bin/sh
# Output recent Polymarket decisions and results for session learning.
# Usage: polymarket-context.sh [workspace_root]
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec python3 - "$WORKSPACE_ROOT" <<'PY'
import json
import os
import sys

workspace_root = sys.argv[1]
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from tools import _polymarket_metrics as metrics

def jsonl_path(rel):
    return os.path.join(workspace_root, rel)

def load_tail(path, n=15):
    rows = metrics.load_jsonl(jsonl_path(path))
    return rows[-n:] if rows else []

decisions = load_tail("data/polymarket-decisions.json")
results = load_tail("data/polymarket-results.json")
summary = metrics.summarize(workspace_root)

ctx = {
    "recent_decisions": [
        {
            "date": d.get("date"),
            "question": (d.get("question") or "")[:80],
            "side": d.get("side"),
            "action": d.get("action"),
            "edge": d.get("edge"),
            "reasoning": (d.get("reasoning") or "")[:120],
        }
        for d in decisions
    ],
    "recent_results": [
        {
            "question": (r.get("question") or "")[:80],
            "won": r.get("won"),
            "pnl_amount": r.get("pnl_amount"),
        }
        for r in results
    ],
    "summary": {
        "bankroll": round(summary["current_bankroll"], 2),
        "resolved_count": summary["resolved_count"],
        "accuracy": round(summary["accuracy"], 4),
        "skip_count": summary["skip_count"],
        "average_edge": summary["average_edge"],
    },
}
print(json.dumps(ctx, indent=2))
PY

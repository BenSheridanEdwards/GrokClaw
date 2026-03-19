#!/bin/sh
# Run a deterministic local smoke test of the Polymarket paper-trading loop.
# Usage: polymarket-smoke.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

mkdir -p "$TMPDIR/data" "$TMPDIR/memory"
cp "$WORKSPACE_ROOT/memory/MEMORY.md" "$TMPDIR/memory/MEMORY.md"
export PYTHONPATH="$WORKSPACE_ROOT${PYTHONPATH:+:$PYTHONPATH}"

python3 - "$TMPDIR" <<'PY'
import sys

from tools import _polymarket_trade as trade

workspace_root = sys.argv[1]
trade.stage_candidate(
    workspace_root,
    {
        "date": "2026-03-14",
        "market_id": "smoke-market-1",
        "question": "Smoke test market",
        "odds_yes": 0.52,
        "odds_no": 0.48,
        "volume": 50000,
        "endDate": "2026-03-20T00:00:00Z",
    },
)
PY

WORKSPACE_ROOT="$TMPDIR" "$SCRIPT_DIR/polymarket-decide.sh" YES 0.66 0.82 "Smoke test edge from deterministic fixture"

python3 - "$TMPDIR" <<'PY'
import json
import os
import sys

from tools import _polymarket_metrics as metrics

workspace_root = sys.argv[1]
trades_path = os.path.join(workspace_root, "data", "polymarket-trades.json")
results_path = os.path.join(workspace_root, "data", "polymarket-results.json")

with open(trades_path, encoding="utf-8") as handle:
    trade = json.loads(handle.readline())

trade["resolved"] = True
trade["resolved_at"] = "2026-03-14"
with open(trades_path, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(trade) + "\n")

pnl_units = (1.0 / float(trade["odds"])) - 1.0
pnl_amount = round(float(trade["stake_amount"]) * pnl_units, 2)
bankroll_entry = metrics.record_bankroll_event(
    workspace_root,
    {
        "date": "2026-03-14",
        "kind": "resolved_trade",
        "market_id": trade["market_id"],
        "question": trade["question"],
        "delta": pnl_amount,
    },
)
result = {
    "date": trade["date"],
    "resolved_at": "2026-03-14",
    "market_id": trade["market_id"],
    "question": trade["question"],
    "side": trade["side"],
    "odds": trade["odds"],
    "won": True,
    "winning_side": "YES",
    "pnl": round(pnl_units, 4),
    "stake_amount": trade["stake_amount"],
    "pnl_amount": pnl_amount,
    "probability_yes": trade["probability_yes"],
    "model_probability": trade["model_probability"],
    "market_probability": trade["market_probability"],
    "edge": trade["edge"],
    "bankroll_before": bankroll_entry["bankroll_before"],
    "bankroll_after": bankroll_entry["bankroll_after"],
}
with open(results_path, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(result) + "\n")
PY

printf '\n== Digest ==\n'
WORKSPACE_ROOT="$TMPDIR" POLYMARKET_DRY_RUN=1 "$SCRIPT_DIR/polymarket-digest.sh"
printf '\n== Report ==\n'
WORKSPACE_ROOT="$TMPDIR" "$SCRIPT_DIR/polymarket-report.sh"
printf '\nSmoke workspace: %s\n' "$TMPDIR"

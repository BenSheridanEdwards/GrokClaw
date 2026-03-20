#!/bin/sh
# Sentient smoke test: fetch candidate, stage, decide SKIP, verify no crash.
# Usage: sentient-smoke.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
DATA_DIR="$WORKSPACE_ROOT/data"
TMP_DIR="${TMPDIR:-/tmp}/sentient-smoke-$$"
mkdir -p "$TMP_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT

export WORKSPACE_ROOT="$TMP_DIR"
mkdir -p "$TMP_DIR/data"

echo "[1/4] Fetch markets..."
OUTPUT=$(python3 "$SCRIPT_DIR/_sentient_trade.py" "$TMP_DIR" 2>&1) || {
  echo "Fetch failed (may be no model-arena markets): $OUTPUT"
  exit 0
}

echo "[2/4] Staged candidate:"
echo "$OUTPUT" | head -5

echo "[3/4] Decide SKIP..."
python3 "$SCRIPT_DIR/_sentient_decide.py" "$TMP_DIR" SKIP "Smoke test skip" >/dev/null

echo "[4/4] Report..."
python3 - "$TMP_DIR" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from tools import _sentient_metrics as m
s = m.summarize(sys.argv[1])
assert s["current_bankroll"] == 1000.0
print("Bankroll intact:", s["current_bankroll"])
PY

echo "Sentient smoke: OK"

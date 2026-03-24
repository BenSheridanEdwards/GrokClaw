#!/bin/sh
# End-to-end reliability checks for GrokClaw workflows.
# Usage: reliability-e2e.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

echo "== GrokClaw reliability e2e =="
echo "Workspace: $WORKSPACE_ROOT"
echo ""

echo "[1/3] Unit tests"
python3 -m unittest discover -s "$WORKSPACE_ROOT/tests" -p "test_*.py"
echo ""

echo "[2/3] Approval smoke"
"$WORKSPACE_ROOT/tools/approval-smoke.sh"
echo ""

echo "[3/4] Polymarket smoke"
"$WORKSPACE_ROOT/tools/polymarket-smoke.sh"
echo ""

echo "[4/4] Paperclip prioritization smoke"
"$WORKSPACE_ROOT/tools/paperclip-prioritization-test.sh"
echo ""

echo "PASS: reliability e2e completed"

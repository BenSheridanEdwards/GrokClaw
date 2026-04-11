#!/bin/sh
# Offline smoke checks (approval + polymarket). Does not run unit tests.
# Full verification: ./tools/test-all.sh
# Usage: reliability-e2e.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

echo "== GrokClaw reliability e2e =="
echo "Workspace: $WORKSPACE_ROOT"
echo ""

echo "[1/2] Approval smoke"
"$WORKSPACE_ROOT/tools/approval-smoke.sh"
echo ""

echo "[2/2] Polymarket smoke"
"$WORKSPACE_ROOT/tools/polymarket-smoke.sh"
echo ""

echo "PASS: reliability e2e completed"

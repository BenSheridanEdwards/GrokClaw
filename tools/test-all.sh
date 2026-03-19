#!/bin/sh
# Comprehensive local verification runner (unit + e2e + shell syntax).
# Usage: test-all.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

echo "== GrokClaw full test suite =="
echo ""

echo "[1/4] Shell syntax checks"
for script in "$WORKSPACE_ROOT"/tools/*.sh; do
  sh -n "$script"
done
echo "OK"
echo ""

echo "[2/4] Python syntax checks"
python3 -m py_compile "$WORKSPACE_ROOT"/tools/_*.py
echo "OK"
echo ""

echo "[3/4] Unit tests"
python3 -m unittest discover -s "$WORKSPACE_ROOT/tests" -p "test_*.py"
echo ""

echo "[4/4] End-to-end smoke"
"$WORKSPACE_ROOT/tools/reliability-e2e.sh"
echo ""

echo "PASS: all checks succeeded"

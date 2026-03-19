#!/bin/sh
# Smoke test for opencv-copilot semantic search. Target: >80% accuracy on GrokClaw.
# Usage: oc-search-smoke.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
export WORKSPACE_ROOT
export PYTHONPATH="${WORKSPACE_ROOT}${PYTHONPATH:+:$PYTHONPATH}"

OUTPUT=$(mktemp)
trap 'rm -f "$OUTPUT"' EXIT

"$SCRIPT_DIR/opencv-copilot" search "telegram" --limit 10 >"$OUTPUT" 2>&1 || true
"$SCRIPT_DIR/opencv-copilot" search "health" --limit 10 >>"$OUTPUT" 2>&1 || true
"$SCRIPT_DIR/opencv-copilot" search "polymarket" --limit 10 >>"$OUTPUT" 2>&1 || true
"$SCRIPT_DIR/opencv-copilot" search "linear" --limit 10 >>"$OUTPUT" 2>&1 || true

# Expected: each query should find relevant files
HITS=0
TOTAL=4
if grep -q "telegram" "$OUTPUT" && grep -qE "telegram-post|_telegram" "$OUTPUT"; then
  HITS=$((HITS + 1))
fi
if grep -q "health" "$OUTPUT" && grep -qE "health-check|gateway-watchdog" "$OUTPUT"; then
  HITS=$((HITS + 1))
fi
if grep -q "polymarket" "$OUTPUT" && grep -qE "_polymarket|polymarket-" "$OUTPUT"; then
  HITS=$((HITS + 1))
fi
if grep -q "linear" "$OUTPUT" && grep -qE "linear-|_linear" "$OUTPUT"; then
  HITS=$((HITS + 1))
fi

PCT=$((HITS * 100 / TOTAL))
echo "oc-search-smoke: $HITS/$TOTAL queries found expected files (${PCT}%)"

if [ "$PCT" -lt 80 ]; then
  echo "FAIL: accuracy ${PCT}% below 80% threshold" >&2
  echo "Sample output:" >&2
  head -50 "$OUTPUT" >&2
  exit 1
fi
echo "PASS: accuracy ${PCT}%"
exit 0

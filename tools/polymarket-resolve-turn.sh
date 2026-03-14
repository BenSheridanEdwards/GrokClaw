#!/bin/sh
# Resolve paper trades, print the latest report, and alert Slack when promotion becomes eligible.
# Usage: polymarket-resolve-turn.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="/Users/jarvis/.picoclaw/workspace"

"$SCRIPT_DIR/polymarket-resolve.sh"

REPORT_JSON=$("$SCRIPT_DIR/polymarket-report.sh")
printf '%s\n' "$REPORT_JSON"

if python3 - "$REPORT_JSON" <<'PY'
import json
import sys

report = json.loads(sys.argv[1])
sys.exit(0 if report.get("promotion_gate", {}).get("eligible") else 1)
PY
then
  "$WORKSPACE_ROOT/tools/slack-post.sh" "C0ALE1S0LSF" "Polymarket promotion gate passed.
$REPORT_JSON"
fi

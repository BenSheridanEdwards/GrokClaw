#!/bin/sh
# Resolve paper trades, print the latest report, and alert Telegram when promotion becomes eligible.
# Usage: polymarket-resolve-turn.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

"$SCRIPT_DIR/polymarket-resolve.sh"

REPORT_JSON=$("$SCRIPT_DIR/polymarket-report.sh")
printf '%s\n' "$REPORT_JSON"

if python3 - "$WORKSPACE_ROOT" "$REPORT_JSON" <<'PY'
import json
import sys

workspace_root = sys.argv[1]
report = json.loads(sys.argv[2])

if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from tools import _polymarket_metrics as metrics

eligible = report.get("promotion_gate", {}).get("eligible")
should_alert = metrics.should_send_promotion_alert(workspace_root, eligible)
if not eligible:
    metrics.mark_promotion_alert_state(workspace_root, False)
sys.exit(0 if should_alert else 1)
PY
then
  "$WORKSPACE_ROOT/tools/telegram-post.sh" polymarket "Polymarket promotion gate passed.
$REPORT_JSON"
  python3 - "$WORKSPACE_ROOT" <<'PY'
import sys

workspace_root = sys.argv[1]
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from tools import _polymarket_metrics as metrics

metrics.mark_promotion_alert_state(workspace_root, True)
PY
fi

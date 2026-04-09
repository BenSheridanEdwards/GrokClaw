#!/bin/sh
# Workflow reporting layer: consumes audit JSON and escalates via handler/Telegram.
# Usage:
#   cron-workflow-report.sh <job> [audit_json_path]
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
JOB="${1:?usage: cron-workflow-report.sh <job> [audit_json_path]}"
RUN_ID="${CRON_RUN_ID:-$JOB-$(date +%s)-$$}"
INPUT_FILE="${2:-$WORKSPACE_ROOT/data/workflow-health/checks/${JOB}-latest.json}"
OUT_DIR="$WORKSPACE_ROOT/data/workflow-health/reports"
REPORT_FILE="$OUT_DIR/${JOB}-${RUN_ID}.json"
DIAG_LOG="$OUT_DIR/workflow-report-diagnostics.log"

mkdir -p "$OUT_DIR"
if [ ! -f "$INPUT_FILE" ]; then
  exit 0
fi
cp "$INPUT_FILE" "$REPORT_FILE"

HANDLE="$WORKSPACE_ROOT/tools/_workflow_health_handle.py"
if [ -f "$HANDLE" ]; then
  if python3 "$HANDLE" <"$INPUT_FILE" >>"$DIAG_LOG" 2>&1; then
    exit 0
  fi
fi

# Fallback: when handler is unavailable/fails, post unhealthy audit alerts directly.
TELEGRAM_POST="$WORKSPACE_ROOT/tools/telegram-post.sh"
if [ -x "$TELEGRAM_POST" ]; then
  ALERT="$(python3 - "$INPUT_FILE" <<'PY'
import json, sys
path = sys.argv[1]
try:
    payload = json.loads(open(path, encoding="utf-8").read() or "{}")
except Exception:
    print("")
    raise SystemExit(0)
if isinstance(payload, dict) and payload.get("healthy") is False:
    msg = payload.get("alertMessage") or f"Workflow health failure detected for {payload.get('workflow','run')}"
    print(str(msg))
else:
    print("")
PY
)"
  if [ -n "$ALERT" ]; then
    "$TELEGRAM_POST" health "$ALERT" >/dev/null 2>&1 || true
  fi
fi

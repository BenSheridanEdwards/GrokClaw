#!/bin/sh
# Workflow checking layer: produce workflow-health audit JSON for a terminal run.
# Usage:
#   cron-workflow-check.sh <job>
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
JOB="${1:?usage: cron-workflow-check.sh <job>}"
RUN_ID="${CRON_RUN_ID:-$JOB-$(date +%s)-$$}"
OUT_DIR="$WORKSPACE_ROOT/data/workflow-health/checks"
RESULT_FILE="$OUT_DIR/${JOB}-${RUN_ID}.json"
LATEST_FILE="$OUT_DIR/${JOB}-latest.json"
ERR_FILE="$OUT_DIR/${JOB}-${RUN_ID}.err.log"

mkdir -p "$OUT_DIR"

AUDIT="$WORKSPACE_ROOT/tools/_workflow_health.py"
if [ ! -f "$AUDIT" ]; then
  printf '{"healthy":false,"failures":[{"workflow":"%s","kind":"workflow_health_missing","message":"tools/_workflow_health.py missing"}]}\n' "$JOB" >"$RESULT_FILE"
  cp "$RESULT_FILE" "$LATEST_FILE"
  printf '%s\n' "$RESULT_FILE"
  exit 0
fi

if python3 "$AUDIT" audit-one "$JOB" --include-paperclip >"$RESULT_FILE" 2>"$ERR_FILE"; then
  cp "$RESULT_FILE" "$LATEST_FILE"
  rm -f "$ERR_FILE"
  printf '%s\n' "$RESULT_FILE"
  exit 0
fi

ERR_MSG="$(tr '\n' ' ' <"$ERR_FILE" | sed 's/"/\\"/g' 2>/dev/null || true)"
printf '{"healthy":false,"failures":[{"workflow":"%s","kind":"audit_command_failed","message":"%s"}]}\n' "$JOB" "${ERR_MSG:-audit-one failed}" >"$RESULT_FILE"
cp "$RESULT_FILE" "$LATEST_FILE"
printf '%s\n' "$RESULT_FILE"

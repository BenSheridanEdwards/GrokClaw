#!/bin/sh
# Append one structured cron run record for Grok scrutiny (data/cron-runs/*.jsonl).
# Every scheduled agent job should call this as its final step with a factual one-line summary.
#
# Usage:
#   cron-run-record.sh <job_name> <agent> <ok|error|skipped> "<summary>"
#   printf '%s' "summary" | cron-run-record.sh <job_name> <agent> ok -
#
# agent: grok | kimi | alpha (who ran the job)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

[ "$#" -ge 4 ] || {
  echo "usage: cron-run-record.sh <job_name> <agent> <ok|error|skipped> <summary|- for stdin>" >&2
  exit 1
}

JOB="$1"
AGENT="$2"
STATUS="$3"
shift 3

if [ "${1:-}" = "-" ]; then
  SUMMARY=$(cat)
else
  SUMMARY="$*"
fi

case "$STATUS" in ok|error|skipped) ;; *)
  echo "cron-run-record.sh: status must be ok, error, or skipped" >&2
  exit 1
  ;;
esac

DIR="$WORKSPACE_ROOT/data/cron-runs"
DATE=$(date -u +%Y-%m-%d)
FILE="$DIR/${DATE}.jsonl"
mkdir -p "$DIR"

# Resolve Paperclip issue UUID: env wins; else stable per-job file from core workflow prompts.
ISSUE_UUID="${PAPERCLIP_ISSUE_UUID:-}"
if [ -z "$ISSUE_UUID" ]; then
  ISSUE_FILE="$WORKSPACE_ROOT/.openclaw/${JOB}.issue"
  if [ -f "$ISSUE_FILE" ]; then
    ISSUE_UUID=$(tr -d ' \t\n\r' <"$ISSUE_FILE" || true)
  fi
fi

export CRON_JOB="$JOB" CRON_AGENT="$AGENT" CRON_STATUS="$STATUS" CRON_SUMMARY="$SUMMARY" CRON_FILE="$FILE"
python3 <<'PY'
import json, os, datetime

job = os.environ["CRON_JOB"]
agent = os.environ["CRON_AGENT"]
status = os.environ["CRON_STATUS"]
summary = os.environ["CRON_SUMMARY"].strip()
path = os.environ["CRON_FILE"]

ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
rec = {"job": job, "agent": agent, "ts": ts, "status": status, "summary": summary}
line = json.dumps(rec, ensure_ascii=False)
with open(path, "a", encoding="utf-8") as f:
    f.write(line + "\n")
PY

TELEGRAM_POST="$WORKSPACE_ROOT/tools/telegram-post.sh"
LIFECYCLE="$WORKSPACE_ROOT/tools/cron-paperclip-lifecycle.sh"
PAPERCLIP_API="$WORKSPACE_ROOT/tools/paperclip-api.sh"
WORKFLOW_HEALTH_AUDIT="$WORKSPACE_ROOT/tools/_workflow_health.py"
WORKFLOW_HEALTH_HANDLE="$WORKSPACE_ROOT/tools/_workflow_health_handle.py"
TELEGRAM_MESSAGE="[$AGENT] $JOB: $STATUS -- $SUMMARY"
WORKFLOW_HEALTH_READY=0
if [ -f "$WORKFLOW_HEALTH_AUDIT" ] && [ -f "$WORKFLOW_HEALTH_HANDLE" ]; then
  WORKFLOW_HEALTH_READY=1
fi

if [ -n "$ISSUE_UUID" ]; then
  LIFECYCLE_STATUS="$STATUS"
  "$LIFECYCLE" finish "$ISSUE_UUID" "$LIFECYCLE_STATUS" "$SUMMARY"

  if [ "$STATUS" = "error" ] && [ -n "${CRON_ERROR_DETAILS:-}" ]; then
    "$PAPERCLIP_API" comment "$ISSUE_UUID" "Error details: ${CRON_ERROR_DETAILS}"
  fi
fi

if [ "$STATUS" = "error" ] && [ "$WORKFLOW_HEALTH_READY" -eq 0 ]; then
  "$TELEGRAM_POST" health "$TELEGRAM_MESSAGE"
fi

if [ "$WORKFLOW_HEALTH_READY" -eq 1 ]; then
  AUDIT_RESULT="$(mktemp)"
  if python3 "$WORKFLOW_HEALTH_AUDIT" audit-one "$JOB" >"$AUDIT_RESULT" 2>/dev/null; then
    python3 "$WORKFLOW_HEALTH_HANDLE" <"$AUDIT_RESULT" >/dev/null 2>&1 || true
  fi
  rm -f "$AUDIT_RESULT"
fi

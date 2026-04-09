#!/bin/sh
# Append one structured cron run record for Grok scrutiny (data/cron-runs/*.jsonl).
# Every scheduled agent job should call this as its final step with a factual one-line summary.
#
# Usage:
#   cron-run-record.sh <job_name> <agent> <started|ok|error|skipped> "<summary>"
#   printf '%s' "summary" | cron-run-record.sh <job_name> <agent> ok -
#
# agent: grok | kimi | alpha (who ran the job)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

[ "$#" -ge 4 ] || {
  echo "usage: cron-run-record.sh <job_name> <agent> <started|ok|error|skipped> <summary|- for stdin>" >&2
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

case "$STATUS" in started|ok|error|skipped) ;; *)
  echo "cron-run-record.sh: status must be started, ok, error, or skipped" >&2
  exit 1
  ;;
esac

DIR="$WORKSPACE_ROOT/data/cron-runs"
DATE=$(date -u +%Y-%m-%d)
FILE="$DIR/${DATE}.jsonl"
mkdir -p "$DIR"
DIAG_LOG="$DIR/cron-run-record-diagnostics.log"

diag() {
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  printf '%s %s\n' "$ts" "$*" >>"$DIAG_LOG" 2>/dev/null || true
}

# Resolve Paperclip issue UUID: on-disk file wins (updated on every lifecycle start); env is often stale
# across long agent turns and can close the wrong issue while a newer run's issue stays in_progress.
ISSUE_FILE="$WORKSPACE_ROOT/.openclaw/${JOB}.issue"
ISSUE_UUID=""
if [ -f "$ISSUE_FILE" ]; then
  ISSUE_UUID=$(tr -d ' \t\n\r' <"$ISSUE_FILE" || true)
fi
if [ -z "$ISSUE_UUID" ]; then
  ISSUE_UUID="${PAPERCLIP_ISSUE_UUID:-}"
fi

export CRON_JOB="$JOB" CRON_AGENT="$AGENT" CRON_STATUS="$STATUS" CRON_SUMMARY="$SUMMARY" CRON_FILE="$FILE" CRON_RUN_ID_VALUE="${CRON_RUN_ID:-}"
python3 <<'PY'
import json, os, datetime

job = os.environ["CRON_JOB"]
agent = os.environ["CRON_AGENT"]
status = os.environ["CRON_STATUS"]
summary = os.environ["CRON_SUMMARY"].strip()
path = os.environ["CRON_FILE"]
run_id = os.environ.get("CRON_RUN_ID_VALUE", "").strip()

ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
rec = {"job": job, "agent": agent, "ts": ts, "status": status, "summary": summary}
if run_id:
    rec["runId"] = run_id
line = json.dumps(rec, ensure_ascii=False)
with open(path, "a", encoding="utf-8") as f:
    f.write(line + "\n")
PY

if [ "$STATUS" = "started" ]; then
  exit 0
fi

TELEGRAM_POST="$WORKSPACE_ROOT/tools/telegram-post.sh"
LIFECYCLE="$WORKSPACE_ROOT/tools/cron-paperclip-lifecycle.sh"
PAPERCLIP_API="$WORKSPACE_ROOT/tools/paperclip-api.sh"

if [ -n "$ISSUE_UUID" ]; then
  LIFECYCLE_STATUS="$STATUS"
  if ! "$LIFECYCLE" finish "$ISSUE_UUID" "$LIFECYCLE_STATUS" "$SUMMARY"; then
    diag "paperclip_finish_failed job=$JOB issue=$ISSUE_UUID status=$LIFECYCLE_STATUS"
  fi

  if [ -n "${CRON_RUN_ID:-}" ]; then
    if ! "$PAPERCLIP_API" comment "$ISSUE_UUID" "Run ID: ${CRON_RUN_ID} | terminal status: ${STATUS}"; then
      diag "paperclip_runid_comment_failed job=$JOB issue=$ISSUE_UUID run_id=${CRON_RUN_ID}"
    fi
  fi

  if [ "$STATUS" = "error" ] && [ -n "${CRON_ERROR_DETAILS:-}" ]; then
    if ! "$PAPERCLIP_API" comment "$ISSUE_UUID" "Error details: ${CRON_ERROR_DETAILS}"; then
      diag "paperclip_comment_failed job=$JOB issue=$ISSUE_UUID"
    fi
  fi
fi

# The workflow checking and reporting layers are intentionally separated:
# - tools/cron-workflow-check.sh owns workflow-health checks
# - tools/cron-workflow-report.sh owns alert/report handling

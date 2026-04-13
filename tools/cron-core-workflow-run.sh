#!/usr/bin/env bash
# Orchestrator for North Star core cron workflows: Paperclip start, cron-run-record started,
# one openclaw agent turn from docs/prompts/cron-work-<job>.md, then always terminal
# cron-run-record + Paperclip finish (via cron-run-record.sh) on EXIT.
#
# Usage: ./tools/cron-core-workflow-run.sh <job_name> <agent_id>
# Env:
#   WORKSPACE_ROOT          Repo root (default: parent of tools/)
#   OPENCLAW_AGENT_TIMEOUT_SECONDS  Timeout for openclaw agent (seconds, default 600)
#   OPENCLAW_BIN            Override openclaw executable (for tests)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
cd "$WORKSPACE_ROOT"

JOB="${1:?usage: cron-core-workflow-run.sh <job_name> <agent_id>}"
AGENT="${2:?usage: cron-core-workflow-run.sh <job_name> <agent_id>}"

case "$JOB" in
  grok-daily-brief | alpha-polymarket) ;;
  *)
    echo "cron-core-workflow-run.sh: unknown job: $JOB" >&2
    exit 2
    ;;
esac

ISSUE_FILE_ABS="$WORKSPACE_ROOT/.openclaw/${JOB}.issue"
PROMPT_FILE="$WORKSPACE_ROOT/docs/prompts/cron-work-${JOB}.md"
LOG_DIR="$WORKSPACE_ROOT/data/cron-runs"
LOG_FILE="$LOG_DIR/orchestrator-${JOB}.log"
SESSION_ID="cron-core-${JOB}-$(date +%s)-$$"
CRON_RUN_ID="${CRON_RUN_ID:-cron-core-${JOB}-$(date +%s)-$$}"
if [ "$JOB" = "alpha-polymarket" ]; then
  TIMEOUT_SEC="${OPENCLAW_AGENT_TIMEOUT_SECONDS_ALPHA:-${OPENCLAW_AGENT_TIMEOUT_SECONDS:-900}}"
  RETRIES="${OPENCLAW_AGENT_RETRIES_ALPHA:-${OPENCLAW_AGENT_RETRIES:-2}}"
  RETRY_BACKOFF_SEC="${OPENCLAW_AGENT_RETRY_BACKOFF_SECONDS_ALPHA:-${OPENCLAW_AGENT_RETRY_BACKOFF_SECONDS:-3}}"
else
  TIMEOUT_SEC="${OPENCLAW_AGENT_TIMEOUT_SECONDS:-600}"
  RETRIES="${OPENCLAW_AGENT_RETRIES:-1}"
  RETRY_BACKOFF_SEC="${OPENCLAW_AGENT_RETRY_BACKOFF_SECONDS:-5}"
fi
RETRY_TELEMETRY_FILE="$LOG_DIR/${JOB}-retry-telemetry.jsonl"
LOCK_DIR="$WORKSPACE_ROOT/.openclaw/locks/cron-core-${JOB}.lock"
LOCK_ACQUIRED=0

AGENT_EXIT=""
_CRON_CORE_FINALIZED=""

_finalize() {
  if [ -n "${_CRON_CORE_FINALIZED:-}" ]; then
    return 0
  fi
  _CRON_CORE_FINALIZED=1

  local ts status summary
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  if [ "${AGENT_EXIT:-}" = "" ]; then
    status="error"
    summary="orchestrator: ended before agent exit code captured"
    export CRON_ERROR_DETAILS="orchestrator: abnormal termination before agent completed"
  elif [ "${AGENT_EXIT}" -eq 0 ]; then
    status="ok"
    summary="orchestrator: agent completed successfully"
    unset CRON_ERROR_DETAILS 2>/dev/null || true
  else
    status="error"
    summary="orchestrator: agent exited ${AGENT_EXIT}"
    export CRON_ERROR_DETAILS="openclaw agent exited ${AGENT_EXIT}"
  fi

  {
    printf '%s job=%s agent=%s agent_exit=%s terminal_status=%s %s\n' \
      "$ts" "$JOB" "$AGENT" "${AGENT_EXIT:-na}" "$status" "$summary"
  } >>"$LOG_FILE" 2>/dev/null || true

  # Deterministic evidence contract backfill: ensures required artifacts/telegram evidence
  # exist even when the model returns narrative output without executing operational commands.
  EVIDENCE_PATH="$WORKSPACE_ROOT/tools/cron-workflow-evidence.sh"
  EVIDENCE_FILE=""
  EVIDENCE_MAX_SEVERITY=""
  if [ -x "$EVIDENCE_PATH" ]; then
    EVIDENCE_FILE="$(env CRON_RUN_ID="${CRON_RUN_ID}" "$EVIDENCE_PATH" "$JOB" "$AGENT" 2>/dev/null || true)"
    EVIDENCE_FILE="$(printf '%s' "$EVIDENCE_FILE" | tr -d '\r\n')"
    if [ -n "$EVIDENCE_FILE" ] && [ -f "$EVIDENCE_FILE" ]; then
      EVIDENCE_MAX_SEVERITY="$(
        python3 - "$EVIDENCE_FILE" <<'PY'
import json, sys
path = sys.argv[1]
try:
    payload = json.loads(open(path, encoding="utf-8").read() or "{}")
except Exception:
    print("ok")
    raise SystemExit(0)
print(payload.get("maxSeverity", "ok"))
PY
      )"
      EVIDENCE_MAX_SEVERITY="${EVIDENCE_MAX_SEVERITY:-ok}"
    fi
  fi

  if [ "$status" = "ok" ] && [ "${EVIDENCE_MAX_SEVERITY:-ok}" = "error" ]; then
    status="error"
    summary="orchestrator: evidence repairs applied (critical)"
    export CRON_ERROR_DETAILS="evidence contract auto-repaired missing primary outputs"
  fi

  # Terminal record + Paperclip finish (cron-run-record.sh); tolerate failure so trap completes.
  # shellcheck disable=SC2086
  env CRON_ERROR_DETAILS="${CRON_ERROR_DETAILS:-}" CRON_RUN_ID="${CRON_RUN_ID}" \
    "$WORKSPACE_ROOT/tools/cron-run-record.sh" "$JOB" "$AGENT" "$status" "$summary" || true

  # Layered checks/reporting:
  # - cron-workflow-check.sh computes workflow-health evidence
  # - cron-workflow-report.sh handles escalation/reporting from that evidence
  CHECK_PATH="$WORKSPACE_ROOT/tools/cron-workflow-check.sh"
  REPORT_PATH="$WORKSPACE_ROOT/tools/cron-workflow-report.sh"
  CHECK_RESULT=""
  if [ -x "$CHECK_PATH" ]; then
    CHECK_RESULT="$(env CRON_RUN_ID="${CRON_RUN_ID}" "$CHECK_PATH" "$JOB" 2>/dev/null || true)"
    CHECK_RESULT="$(printf '%s' "$CHECK_RESULT" | tr -d '\r\n')"
  fi
  if [ -x "$REPORT_PATH" ]; then
    env CRON_RUN_ID="${CRON_RUN_ID}" "$REPORT_PATH" "$JOB" "${CHECK_RESULT:-}" || true
  fi

  rm -f "$ISSUE_FILE_ABS"
  if [ "$LOCK_ACQUIRED" -eq 1 ]; then
    rmdir "$LOCK_DIR" 2>/dev/null || true
  fi
}

trap '_finalize' EXIT

mkdir -p "$WORKSPACE_ROOT/.openclaw" "$LOG_DIR"
mkdir -p "$WORKSPACE_ROOT/.openclaw/locks"

LOCK_STALE_SECONDS="${OPENCLAW_LOCK_STALE_SECONDS:-1800}"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  lock_age="$(python3 -c "
import os, time
try:
    age = time.time() - os.path.getmtime('$LOCK_DIR')
    print(int(age))
except Exception:
    print(0)
" 2>/dev/null || echo 0)"
  if [ "$lock_age" -ge "$LOCK_STALE_SECONDS" ]; then
    rmdir "$LOCK_DIR" 2>/dev/null || true
    if ! mkdir "$LOCK_DIR" 2>/dev/null; then
      _CRON_CORE_FINALIZED=1
      env CRON_RUN_ID="$CRON_RUN_ID" \
        "$WORKSPACE_ROOT/tools/cron-run-record.sh" "$JOB" "$AGENT" skipped "already running: lock exists for ${JOB}" || true
      exit 0
    fi
    {
      printf '%s job=%s stale_lock_reclaimed age_seconds=%s\n' \
        "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$JOB" "$lock_age"
    } >>"$LOG_FILE" 2>/dev/null || true
  else
    _CRON_CORE_FINALIZED=1
    env CRON_RUN_ID="$CRON_RUN_ID" \
      "$WORKSPACE_ROOT/tools/cron-run-record.sh" "$JOB" "$AGENT" skipped "already running: lock exists for ${JOB}" || true
    exit 0
  fi
fi
LOCK_ACQUIRED=1

if [ ! -f "$PROMPT_FILE" ]; then
  echo "cron-core-workflow-run.sh: missing prompt file: $PROMPT_FILE" >&2
  AGENT_EXIT=2
  exit 2
fi

# Pre-flight: verify OpenClaw runtime config has a non-empty message payload for this job.
# A missing message causes the agent to start with no instructions and silently produce
# no output, which the evidence contract then flags as a critical error.
# If drift is detected, auto-sync and restart the gateway before aborting — so the NEXT
# scheduled run succeeds without manual intervention.
OPENCLAW_CRON_JOBS="${OPENCLAW_CRON_JOBS_PATH:-${HOME}/.openclaw/cron/jobs.json}"
if [ -f "$OPENCLAW_CRON_JOBS" ]; then
  PAYLOAD_OK="$(python3 -c "
import json, sys
try:
    data = json.loads(open('$OPENCLAW_CRON_JOBS', encoding='utf-8').read())
    for job in data.get('jobs', []):
        if job.get('name') == '$JOB':
            msg = (job.get('payload') or {}).get('message') or ''
            if msg.strip():
                print('ok')
                sys.exit(0)
    print('missing')
except Exception as e:
    print('error: ' + str(e))
" 2>/dev/null || echo "error")"
  case "$PAYLOAD_OK" in
    ok) ;;
    missing)
      echo "cron-core-workflow-run.sh: runtime config missing payload for '$JOB' — auto-syncing..." >&2
      {
        printf '%s job=%s preflight_fail=missing_payload_message action=auto_sync\n' \
          "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$JOB"
      } >>"$LOG_FILE" 2>/dev/null || true
      # Auto-repair: sync from repo and restart gateway so the next cron fire succeeds.
      if "$WORKSPACE_ROOT/tools/sync-cron-jobs.sh" --restart >/dev/null 2>&1; then
        echo "cron-core-workflow-run.sh: auto-sync succeeded; aborting this run (next scheduled run will use fixed config)" >&2
      else
        echo "cron-core-workflow-run.sh: auto-sync FAILED; run manually: ./tools/sync-cron-jobs.sh --restart" >&2
      fi
      AGENT_EXIT=3
      exit 3
      ;;
    *)
      echo "cron-core-workflow-run.sh: warning: could not verify runtime payload for '$JOB': $PAYLOAD_OK" >&2
      ;;
  esac
fi

UUID="$("$WORKSPACE_ROOT/tools/cron-paperclip-lifecycle.sh" start "$JOB" "$AGENT")"
printf '%s' "$UUID" >"$ISSUE_FILE_ABS"

env CRON_RUN_ID="$CRON_RUN_ID" \
  "$WORKSPACE_ROOT/tools/cron-run-record.sh" "$JOB" "$AGENT" started 'run started'

set +e
if [ "$JOB" = "alpha-polymarket" ] && [ -x "$WORKSPACE_ROOT/tools/alpha-polymarket-deterministic.sh" ]; then
  CRON_RUN_ID="$CRON_RUN_ID" "$WORKSPACE_ROOT/tools/alpha-polymarket-deterministic.sh"
else
  OPENCLAW_AGENT_RETRIES="$RETRIES" OPENCLAW_AGENT_RETRY_BACKOFF_SECONDS="$RETRY_BACKOFF_SEC" \
    CRON_RUN_ID="$CRON_RUN_ID" python3 "$SCRIPT_DIR/_cron_openclaw_agent.py" "$PROMPT_FILE" \
    --agent "$AGENT" \
    --session-id "$SESSION_ID" \
    --timeout "$TIMEOUT_SEC" \
    --retries "$RETRIES" \
    --retry-backoff "$RETRY_BACKOFF_SEC" \
    --telemetry-file "$RETRY_TELEMETRY_FILE" \
    --cwd "$WORKSPACE_ROOT"
fi
AGENT_EXIT=$?
set -e

exit "$AGENT_EXIT"

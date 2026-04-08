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
  grok-daily-brief | grok-openclaw-research | alpha-polymarket) ;;
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
TIMEOUT_SEC="${OPENCLAW_AGENT_TIMEOUT_SECONDS:-600}"

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

  # Terminal record + Paperclip finish (cron-run-record.sh); tolerate failure so trap completes.
  # shellcheck disable=SC2086
  env CRON_ERROR_DETAILS="${CRON_ERROR_DETAILS:-}" \
    "$WORKSPACE_ROOT/tools/cron-run-record.sh" "$JOB" "$AGENT" "$status" "$summary" || true

  rm -f "$ISSUE_FILE_ABS"
}

trap '_finalize' EXIT

mkdir -p "$WORKSPACE_ROOT/.openclaw" "$LOG_DIR"

if [ ! -f "$PROMPT_FILE" ]; then
  echo "cron-core-workflow-run.sh: missing prompt file: $PROMPT_FILE" >&2
  AGENT_EXIT=2
  exit 2
fi

UUID="$("$WORKSPACE_ROOT/tools/cron-paperclip-lifecycle.sh" start "$JOB" "$AGENT")"
printf '%s' "$UUID" >"$ISSUE_FILE_ABS"

"$WORKSPACE_ROOT/tools/cron-run-record.sh" "$JOB" "$AGENT" started 'run started'

set +e
python3 "$SCRIPT_DIR/_cron_openclaw_agent.py" "$PROMPT_FILE" \
  --agent "$AGENT" \
  --session-id "$SESSION_ID" \
  --timeout "$TIMEOUT_SEC" \
  --cwd "$WORKSPACE_ROOT"
AGENT_EXIT=$?
set -e

exit "$AGENT_EXIT"

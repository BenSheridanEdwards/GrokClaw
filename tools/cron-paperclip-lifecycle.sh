#!/bin/sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
PAPERCLIP_API="$WORKSPACE_ROOT/tools/paperclip-api.sh"

# Only the four core GrokClaw cron workflows may create Paperclip run issues.
is_core_job() {
  case "$1" in
    grok-daily-brief|grok-openclaw-research|alpha-polymarket|kimi-polymarket) return 0 ;;
    *) return 1 ;;
  esac
}

timestamp_iso() {
  if [ -n "${CRON_PAPERCLIP_NOW:-}" ]; then
    printf '%s\n' "$CRON_PAPERCLIP_NOW"
    return
  fi
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

timestamp_display() {
  python3 - "$1" <<'PY'
import datetime
import sys

raw = sys.argv[1]
dt = datetime.datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
print(dt.strftime("%Y-%m-%d %H:%M UTC"))
PY
}

create_issue() {
  job_name="$1"
  agent="$2"
  python3 "$WORKSPACE_ROOT/tools/_workflow_health.py" paperclip-allowed "$job_name" >/dev/null
  now_iso="$(timestamp_iso)"
  now_display="$(timestamp_display "$now_iso")"
  title="[$job_name] $now_display"
  description="Cron run for $job_name by $agent started at $now_display."

  output="$(PAPERCLIP_NO_ASSIGNEE=1 "$PAPERCLIP_API" create-issue "$title" "$description")"
  issue_id="$(printf '%s\n' "$output" | python3 -c 'import re, sys; text=sys.stdin.read(); match=re.search(r"^ID:\s*(.+)$", text, re.M); print(match.group(1) if match else "")')"
  [ -n "$issue_id" ] || {
    echo "cron-paperclip-lifecycle.sh: failed to parse issue ID" >&2
    exit 1
  }

  "$PAPERCLIP_API" update-issue "$issue_id" in_progress >/dev/null
  printf '%s\n' "$issue_id"
}

finish_issue() {
  issue_id="$1"
  result_status="$2"
  summary="$3"
  now_display="$(timestamp_display "$(timestamp_iso)")"

  case "$result_status" in
    ok)
      issue_status="done"
      ;;
    error)
      issue_status="failed"
      ;;
    skipped)
      issue_status="cancelled"
      ;;
    *)
      echo "usage: cron-paperclip-lifecycle.sh finish <issue-id> <ok|error|skipped> <summary>" >&2
      exit 1
      ;;
  esac

  "$PAPERCLIP_API" update-issue "$issue_id" "$issue_status" >/dev/null
  "$PAPERCLIP_API" comment "$issue_id" "[$now_display] $result_status -- $summary" >/dev/null
}

command="${1:-}"
case "$command" in
  start)
    [ "$#" -eq 3 ] || {
      echo "usage: cron-paperclip-lifecycle.sh start <job-name> <agent>" >&2
      exit 1
    }
    if ! is_core_job "$2"; then
      echo "cron-paperclip-lifecycle.sh: refuse create-issue for non-core job: $2" >&2
      exit 1
    fi
    create_issue "$2" "$3"
    ;;
  finish)
    [ "$#" -ge 4 ] || {
      echo "usage: cron-paperclip-lifecycle.sh finish <issue-id> <ok|error|skipped> <summary>" >&2
      exit 1
    }
    issue_id="$2"
    result_status="$3"
    shift 3
    finish_issue "$issue_id" "$result_status" "$*"
    ;;
  *)
    echo "usage: cron-paperclip-lifecycle.sh <start|finish> ..." >&2
    exit 1
    ;;
esac

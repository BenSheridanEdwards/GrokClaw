#!/bin/sh
# Execute deterministic Telegram action messages in single-poller mode.
# Usage:
#   dispatch-telegram-action.sh "<message text from button>"
#
# Accepted action token formats:
#   merge:<pr-number>:<issue-id>
#   reject:<pr-number>:<issue-id>
#   approve_idea:<n>:<issue-id>
#   approve_suggestion:<n>        — sends the draft Linear ticket for suggestion review
#   approve_linear_draft:<id>     — creates Linear from a pending approved draft
#   reject_linear_draft:<id>      — cancels a pending draft without creating Linear
#   probe:<label>:<id>
#   rerun_workflow:<job-name>         — triggers the named cron workflow immediately
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STATE_DIR="${HOME}/.openclaw/state"
SEEN_FILE="${STATE_DIR}/telegram-action-seen.txt"
LOCK_DIR="${STATE_DIR}/telegram-action-seen.lock"

if [ "$#" -lt 1 ]; then
  echo "usage: dispatch-telegram-action.sh \"<action message>\"" >&2
  exit 1
fi

RAW="$1"
# Allow friendly labels like "Reject | reject:15:GRO-21"
TOKEN="$(printf '%s' "$RAW" | awk -F'|' '{print $NF}' | sed 's/^ *//; s/ *$//')"

ACTION="$(printf '%s' "$TOKEN" | cut -d: -f1)"
PR_NUM="$(printf '%s' "$TOKEN" | cut -d: -f2)"
ISSUE_ID="$(printf '%s' "$TOKEN" | cut -d: -f3)"

python3 "$WORKSPACE_ROOT/tools/_audit_log.py" \
  telegram_incoming "actions" "$RAW" "$TOKEN" >/dev/null 2>&1 || true

mkdir -p "$STATE_DIR"
[ -f "$SEEN_FILE" ] || : >"$SEEN_FILE"

# Acquire a simple lock to avoid duplicate execution races.
acquired=0
while [ "$acquired" -eq 0 ]; do
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    acquired=1
  else
    sleep 0.1
  fi
done
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT INT TERM

if rg -F -x -- "$TOKEN" "$SEEN_FILE" >/dev/null 2>&1; then
  echo "Action already processed, skipping: $TOKEN"
  exit 0
fi

case "$ACTION" in
  probe)
    printf '%s\n' "$TOKEN" >>"$SEEN_FILE"
    echo "Probe action received: $TOKEN"
    ;;
  merge)
    gh pr merge "$PR_NUM" --squash --delete-branch --repo BenSheridanEdwards/GrokClaw
    "$WORKSPACE_ROOT/tools/linear-transition.sh" "$ISSUE_ID" Done
    printf '%s\n' "$TOKEN" >>"$SEEN_FILE"
    echo "Merged PR #$PR_NUM and moved $ISSUE_ID to Done"
    ;;
  reject)
    gh pr comment "$PR_NUM" --repo BenSheridanEdwards/GrokClaw \
      --body "@cursor Changes requested by Ben from Telegram action button. Please revise and mark ready again."
    printf '%s\n' "$TOKEN" >>"$SEEN_FILE"
    echo "Requested revisions on PR #$PR_NUM"
    ;;
  approve_idea)
    "$WORKSPACE_ROOT/tools/linear-transition.sh" "$ISSUE_ID" "In Progress"
    printf '%s\n' "$TOKEN" >>"$SEEN_FILE"
    echo "Idea approved. $ISSUE_ID moved to In Progress"
    ;;
  approve_suggestion)
    SUGGESTION_N="$PR_NUM"
    PENDING_FILE="$WORKSPACE_ROOT/data/pending-suggestion-${SUGGESTION_N}.json"
    if [ ! -f "$PENDING_FILE" ]; then
      echo "Missing pending suggestion file: $PENDING_FILE" >&2
      exit 1
    fi
    TITLE=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('title',''))" "$PENDING_FILE")
    DESC=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('description',''))" "$PENDING_FILE")
    OUTPUT=$("$WORKSPACE_ROOT/tools/approve-suggestion.sh" "$SUGGESTION_N" "$TITLE" "suggestions" "$DESC" 2>&1) || true
    rm -f "$PENDING_FILE"
    printf '%s\n' "$TOKEN" >>"$SEEN_FILE"
    echo "Suggestion #${SUGGESTION_N} approved. Draft sent for Linear review."
    ;;
  approve_linear_draft)
    DRAFT_ID="$PR_NUM"
    "$WORKSPACE_ROOT/tools/linear-draft-approval.sh" create "$DRAFT_ID"
    printf '%s\n' "$TOKEN" >>"$SEEN_FILE"
    echo "Linear draft approved: $DRAFT_ID"
    ;;
  reject_linear_draft)
    DRAFT_ID="$PR_NUM"
    "$WORKSPACE_ROOT/tools/linear-draft-approval.sh" reject "$DRAFT_ID"
    printf '%s\n' "$TOKEN" >>"$SEEN_FILE"
    echo "Linear draft rejected: $DRAFT_ID"
    ;;
  rerun_workflow)
    JOB_NAME="$PR_NUM"
    AGENT="$(python3 -c "
m={'grok-daily-brief':'grok','grok-openclaw-research':'grok','alpha-polymarket':'alpha','kimi-polymarket':'kimi'}
print(m.get('$JOB_NAME','grok'))
")"
    CRON_MSG="$(python3 -c "
import json
jobs=json.load(open('$WORKSPACE_ROOT/cron/jobs.json')).get('jobs',[])
hit=[j for j in jobs if j.get('name')=='$JOB_NAME']
print(hit[0]['payload']['message'] if hit else '')
" 2>/dev/null || echo "")"

    if [ -z "$CRON_MSG" ]; then
      echo "Unknown workflow: $JOB_NAME" >&2
      exit 1
    fi

    printf '%s\n' "$TOKEN" >>"$SEEN_FILE"
    printf '%s\n' "Rerunning $JOB_NAME on $AGENT..." \
      | "$WORKSPACE_ROOT/tools/telegram-post.sh" health 2>/dev/null || true

    OPENCLAW_AGENT_ID="$AGENT" OPENCLAW_MESSAGE="$CRON_MSG" \
      "$WORKSPACE_ROOT/tools/run-openclaw-agent.sh" &
    echo "Triggered rerun of $JOB_NAME on agent $AGENT"
    ;;
  *)
    echo "Unknown action token: $TOKEN" >&2
    exit 1
    ;;
esac

#!/usr/bin/env bash
set -euo pipefail

PAPERCLIP_API="http://127.0.0.1:3100/api"
TASK_ID="${PAPERCLIP_TASK_ID:-}"
RUN_ID="${PAPERCLIP_RUN_ID:-$(date +%s)}"
WORKSPACE="${PAPERCLIP_WORKSPACE_CWD:-/Users/jarvis/Engineering/Projects/GrokClaw}"
WAKE_REASON="${PAPERCLIP_WAKE_REASON:-}"
AGENT_ID="${OPENCLAW_AGENT_ID:-grok}"
MESSAGE_OVERRIDE="${OPENCLAW_MESSAGE:-}"
TIMEOUT_SECONDS="${OPENCLAW_AGENT_TIMEOUT_SECONDS:-}"
RETRIES="${OPENCLAW_AGENT_RETRIES:-0}"

SESSION_KEY="paperclip-ephemeral-${RUN_ID}"

if [ -n "$MESSAGE_OVERRIDE" ]; then
  MESSAGE="$MESSAGE_OVERRIDE"
elif [ -n "$TASK_ID" ]; then
  ISSUE_JSON=$(curl -sf "${PAPERCLIP_API}/issues/${TASK_ID}" 2>/dev/null || echo '{}')
  ISSUE_TITLE=$(echo "$ISSUE_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('title',''))" 2>/dev/null || echo "")
  ISSUE_DESC=$(echo "$ISSUE_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('description','') or '')" 2>/dev/null || echo "")
  ISSUE_ID=$(echo "$ISSUE_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('identifier',''))" 2>/dev/null || echo "")

  MESSAGE="You are Grok, the GrokClaw orchestration agent. Read AGENTS.md for your full operating instructions.

Your assigned task (${ISSUE_ID}): ${ISSUE_TITLE}"

  if [ -n "$ISSUE_DESC" ]; then
    MESSAGE="${MESSAGE}

Description: ${ISSUE_DESC}"
  fi

  if [ -n "$WAKE_REASON" ]; then
    MESSAGE="${MESSAGE}

Wake reason: ${WAKE_REASON}"
  fi

  MESSAGE="${MESSAGE}

Execute this task now. Use your tools to read files, run commands, and complete the work."
else
  MESSAGE="You are Grok, the GrokClaw orchestration agent. Read AGENTS.md for your full operating instructions. Check for any pending work and execute it."
fi

cd "$WORKSPACE"

run_agent() {
  local -a command=(openclaw agent --agent "$AGENT_ID" --message "$MESSAGE" --session-id "$SESSION_KEY")
  if [ -n "$TIMEOUT_SECONDS" ]; then
    command+=(--timeout "$TIMEOUT_SECONDS")
  fi
  "${command[@]}"
}

attempt=0
max_attempts=$((RETRIES + 1))
until run_agent; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge "$max_attempts" ]; then
    exit 1
  fi
  sleep 1
done

#!/bin/sh
# Orchestrate the full approval workflow: Linear ticket → draft PR → Slack reply.
# Usage: approve-suggestion.sh <N> "<title>" <thread_ts> [description]
#        approve-suggestion.sh --dry-run <N> "<title>" <thread_ts> [description]
#
# On failure, posts the error to the Slack thread and exits 1.
# Env:   PICOCLAW_WORKSPACE — workspace root (default: derived from script path)
#        APPROVAL_DRY_RUN   — if set, validate args and print steps without executing
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${PICOCLAW_WORKSPACE:-$(cd "$SCRIPT_DIR/.." && pwd)}"
SLACK_CHANNEL="${SLACK_CHANNEL_ID:-C0ALE1S0LSF}"

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
  shift
fi
if [ "${APPROVAL_DRY_RUN:-0}" = "1" ]; then
  DRY_RUN=1
fi

if [ "$#" -lt 3 ]; then
  echo "usage: $0 [--dry-run] <suggestion-number> \"<title>\" <thread_ts> [description]" >&2
  echo "  thread_ts: Slack thread timestamp (e.g. 1234567890.123456) for reply" >&2
  exit 1
fi

SUGGESTION_NUMBER="$1"
SUGGESTION_TITLE="$2"
THREAD_TS="$3"
DESCRIPTION="${4:-}"

if [ "$DRY_RUN" = "1" ]; then
  echo "[dry-run] Would run:"
  echo "  1. $WORKSPACE_ROOT/tools/linear-ticket.sh $SUGGESTION_NUMBER \"$SUGGESTION_TITLE\" \"$DESCRIPTION\""
  echo "  2. $WORKSPACE_ROOT/tools/create-pr.sh <GRO-XX> \"$SUGGESTION_TITLE\""
  echo "  3. $WORKSPACE_ROOT/tools/slack-post.sh $SLACK_CHANNEL $THREAD_TS \"✅ Suggestion #${SUGGESTION_NUMBER} approved. Linear: <url> PR: <url>\""
  exit 0
fi

# Load .env for API keys
if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

post_error() {
  "$WORKSPACE_ROOT/tools/slack-post.sh" "$SLACK_CHANNEL" "$THREAD_TS" \
    "❌ Approval failed at step $1: $2" 2>/dev/null || true
}

# Step 1: Create Linear ticket
export PICOCLAW_WORKSPACE="$WORKSPACE_ROOT"
LINEAR_OUTPUT=$("$WORKSPACE_ROOT/tools/linear-ticket.sh" \
  "$SUGGESTION_NUMBER" "$SUGGESTION_TITLE" "$DESCRIPTION" 2>&1) || {
  post_error "1 (Linear ticket)" "$LINEAR_OUTPUT"
  echo "$LINEAR_OUTPUT" >&2
  exit 1
}

LINEAR_URL=$(echo "$LINEAR_OUTPUT" | tail -n1)
# Extract GRO-XX from URL (e.g. https://linear.app/grokclaw/issue/GRO-18)
LINEAR_ISSUE_ID=$(echo "$LINEAR_URL" | sed -n 's|.*/\(GRO-[0-9]*\)$|\1|p')
if [ -z "$LINEAR_ISSUE_ID" ]; then
  post_error "1 (Linear ticket)" "Could not parse issue ID from: $LINEAR_URL"
  exit 1
fi

# Step 2: Scaffold draft PR
PR_OUTPUT=$("$WORKSPACE_ROOT/tools/create-pr.sh" "$LINEAR_ISSUE_ID" "$SUGGESTION_TITLE" 2>&1) || {
  post_error "2 (create PR)" "$PR_OUTPUT"
  echo "$PR_OUTPUT" >&2
  exit 1
}

PR_URL=$(echo "$PR_OUTPUT" | tail -n1)

# Step 3: Report in Slack
SLACK_MSG="✅ Suggestion #${SUGGESTION_NUMBER} approved.
Linear: ${LINEAR_URL}
PR: ${PR_URL}
Cursor is on it."

"$WORKSPACE_ROOT/tools/slack-post.sh" "$SLACK_CHANNEL" "$THREAD_TS" "$SLACK_MSG" 2>&1 || {
  post_error "3 (Slack reply)" "Could not post success message"
  exit 1
}

echo "Linear: $LINEAR_URL"
echo "PR: $PR_URL"

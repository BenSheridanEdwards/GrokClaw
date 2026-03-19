#!/bin/sh
# Orchestrate the full approval workflow: Linear ticket → Telegram reply.
# Usage: approve-suggestion.sh <N> "<title>" <topic-id> [description]
#        approve-suggestion.sh --dry-run <N> "<title>" <topic-id> [description]
#
# On failure, posts the error to the Telegram topic and exits 1.
# Env:   WORKSPACE_ROOT — workspace root (default: derived from script path)
#        APPROVAL_DRY_RUN   — if set, validate args and print steps without executing
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TELEGRAM_TOPIC="${TELEGRAM_TOPIC_SUGGESTIONS:-suggestions}"

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
  shift
fi
if [ "${APPROVAL_DRY_RUN:-0}" = "1" ]; then
  DRY_RUN=1
fi

if [ "$#" -lt 3 ]; then
  echo "usage: $0 [--dry-run] <suggestion-number> \"<title>\" <topic-id> [description]" >&2
  echo "  topic-id: Telegram topic name or numeric ID for reply" >&2
  exit 1
fi

SUGGESTION_NUMBER="$1"
SUGGESTION_TITLE="$2"
TOPIC_ID="$3"
DESCRIPTION="${4:-}"

if [ "$DRY_RUN" = "1" ]; then
  echo "[dry-run] Would run:"
  echo "  1. $WORKSPACE_ROOT/tools/linear-ticket.sh $SUGGESTION_NUMBER \"$SUGGESTION_TITLE\" \"$DESCRIPTION\""
  echo "  2. $WORKSPACE_ROOT/tools/telegram-post.sh $TELEGRAM_TOPIC \"✅ Suggestion #${SUGGESTION_NUMBER} approved. Linear: <url>. Cursor is on it.\""
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
  RETRY_DISABLE_ALERT=1 "$WORKSPACE_ROOT/tools/retry.sh" --max 2 --delay 1 --alert "$TELEGRAM_TOPIC" -- \
    "$WORKSPACE_ROOT/tools/telegram-post.sh" "$TELEGRAM_TOPIC" \
    "❌ Approval failed at step $1: $2" 2>/dev/null || true
}

# Step 1: Create Linear ticket
export WORKSPACE_ROOT="$WORKSPACE_ROOT"
LINEAR_OUTPUT=$(RETRY_DISABLE_ALERT=1 "$WORKSPACE_ROOT/tools/retry.sh" --max 3 --delay 2 --alert "$TELEGRAM_TOPIC" -- "$WORKSPACE_ROOT/tools/linear-ticket.sh" \
  "$SUGGESTION_NUMBER" "$SUGGESTION_TITLE" "$DESCRIPTION" 2>&1) || {
  post_error "1 (Linear ticket)" "$LINEAR_OUTPUT"
  echo "$LINEAR_OUTPUT" >&2
  exit 1
}

LINEAR_URL=$(echo "$LINEAR_OUTPUT" | tail -n1)
LINEAR_ISSUE_ID=$(echo "$LINEAR_URL" | sed -n 's|.*/\(GRO-[0-9]*\).*|\1|p')
if [ -z "$LINEAR_ISSUE_ID" ]; then
  post_error "1 (Linear ticket)" "Could not parse issue ID from: $LINEAR_URL"
  exit 1
fi

# Step 2: Report in Telegram
TELEGRAM_MSG="✅ Suggestion #${SUGGESTION_NUMBER} approved.
Linear: ${LINEAR_URL}
Cursor is on it."

RETRY_DISABLE_ALERT=1 "$WORKSPACE_ROOT/tools/retry.sh" --max 3 --delay 2 --alert "$TELEGRAM_TOPIC" -- "$WORKSPACE_ROOT/tools/telegram-post.sh" "$TELEGRAM_TOPIC" "$TELEGRAM_MSG" 2>&1 || {
  post_error "2 (Telegram reply)" "Could not post success message"
  exit 1
}

echo "Linear: $LINEAR_URL"

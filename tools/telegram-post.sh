#!/bin/sh
# Post a message to a Telegram group topic.
# Usage:
#   telegram-post.sh <topic-id> <message>
#   telegram-post.sh <topic-id>   # stdin, or TELEGRAM_MESSAGE if set when stdin would be empty
#   echo "text" | telegram-post.sh <topic-id>
#
# Messages with $ amounts (e.g. $1,100) must NOT be passed in double quotes on the shell
# command line — the shell will expand $1, $2, etc. Prefer one of:
#   printf '%s\n' 'Alpha: Bitcoin at $58,100' | ./tools/telegram-post.sh polymarket
#   TELEGRAM_MESSAGE='Alpha: Bitcoin at $58,100' ./tools/telegram-post.sh polymarket
#   ./tools/telegram-post.sh polymarket <<'TG'
#   Alpha: Bitcoin at $58,100
#   TG
#
# Topic shortcuts (resolved from .env):
#   suggestions | polymarket | health | pr-reviews
#
# Env: WORKSPACE_ROOT, TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ID,
#      TELEGRAM_TOPIC_SUGGESTIONS, TELEGRAM_TOPIC_POLYMARKET,
#      TELEGRAM_TOPIC_HEALTH, TELEGRAM_TOPIC_PR_REVIEWS
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:?TELEGRAM_BOT_TOKEN not set}"
TELEGRAM_GROUP_ID="${TELEGRAM_GROUP_ID:?TELEGRAM_GROUP_ID not set}"

if [ "$#" -lt 1 ]; then
  echo "usage: telegram-post.sh <topic-id|name> [message]" >&2
  exit 1
fi

RAW_TOPIC="$1"; shift

case "$RAW_TOPIC" in
  suggestions|daily-suggestions) TOPIC_ID="${TELEGRAM_TOPIC_SUGGESTIONS:-2}" ;;
  polymarket)                    TOPIC_ID="${TELEGRAM_TOPIC_POLYMARKET:-3}" ;;
  health|health-alerts)          TOPIC_ID="${TELEGRAM_TOPIC_HEALTH:-4}" ;;
  pr-reviews)                    TOPIC_ID="${TELEGRAM_TOPIC_PR_REVIEWS:-5}" ;;
  [0-9]*)                        TOPIC_ID="$RAW_TOPIC" ;;
  *)
    echo "unknown topic: $RAW_TOPIC" >&2
    exit 1
    ;;
esac

if [ "$#" -gt 0 ]; then
  MESSAGE="$*"
elif [ -n "${TELEGRAM_MESSAGE:-}" ]; then
  MESSAGE="$TELEGRAM_MESSAGE"
else
  MESSAGE=$(cat)
fi

attempt=1
delay=1
max_attempts=3
last_error=""
while [ "$attempt" -le "$max_attempts" ]; do
  if post_output="$(python3 "$WORKSPACE_ROOT/tools/_telegram_post.py" \
    "$TELEGRAM_BOT_TOKEN" "$TELEGRAM_GROUP_ID" "$TOPIC_ID" "$MESSAGE" 2>&1)"; then
    [ -n "$post_output" ] && printf '%s\n' "$post_output"
    python3 "$WORKSPACE_ROOT/tools/_audit_log.py" \
      telegram_post "$RAW_TOPIC" "$MESSAGE" "$TOPIC_ID" >/dev/null 2>&1 || true
    exit 0
  fi
  last_error="$post_output"
  if [ "$attempt" -ge "$max_attempts" ]; then
    break
  fi
  sleep "$delay"
  delay=$((delay * 2))
  attempt=$((attempt + 1))
done

python3 "$WORKSPACE_ROOT/tools/_audit_log.py" \
  telegram_post_failed "$RAW_TOPIC" "$MESSAGE" "$TOPIC_ID" >/dev/null 2>&1 || true
[ -n "$last_error" ] && printf '%s\n' "$last_error" >&2
echo "telegram-post.sh: failed to deliver message after ${max_attempts} attempts" >&2
exit 1

#!/bin/sh
# Post a message to a Telegram group topic.
# Usage:
#   telegram-post.sh <topic-id> <message>
#   telegram-post.sh <topic-id> -- read message from stdin
#   echo "text" | telegram-post.sh <topic-id>
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
  sentient)                      TOPIC_ID="${TELEGRAM_TOPIC_SENTIENT:-${TELEGRAM_TOPIC_POLYMARKET:-3}}" ;;
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
else
  MESSAGE=$(cat)
fi

attempt=1
delay=1
max_attempts=3
while [ "$attempt" -le "$max_attempts" ]; do
  if python3 "$WORKSPACE_ROOT/tools/_telegram_post.py" \
    "$TELEGRAM_BOT_TOKEN" "$TELEGRAM_GROUP_ID" "$TOPIC_ID" "$MESSAGE"; then
    exit 0
  fi
  if [ "$attempt" -ge "$max_attempts" ]; then
    break
  fi
  sleep "$delay"
  delay=$((delay * 2))
  attempt=$((attempt + 1))
done

echo "telegram-post.sh: failed to deliver message after ${max_attempts} attempts" >&2
exit 1

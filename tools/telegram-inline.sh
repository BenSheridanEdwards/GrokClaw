#!/bin/sh
# Send Telegram message with single-poller action buttons.
# Usage:
#   telegram-inline.sh <topic-id|name> "<message>" '<button-json>' [parse_mode]
#
# parse_mode: Markdown (default), HTML, or plain (no formatting)
# button-json example:
#   '[{"text":"Approve","callback_data":"approve:12:GRO-21"}]'
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

if [ "$#" -lt 3 ]; then
  echo "usage: telegram-inline.sh <topic-id|name> <message> <button-json>" >&2
  exit 1
fi

RAW_TOPIC="$1"
MESSAGE="$2"
BUTTON_JSON="$3"
PARSE_MODE="${4:-Markdown}"

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

"$WORKSPACE_ROOT/tools/retry.sh" --max 3 --delay 1 --alert health -- \
  python3 "$WORKSPACE_ROOT/tools/_telegram_inline.py" \
  "$TELEGRAM_BOT_TOKEN" "$TELEGRAM_GROUP_ID" "$TOPIC_ID" "$MESSAGE" "$BUTTON_JSON" "$PARSE_MODE"

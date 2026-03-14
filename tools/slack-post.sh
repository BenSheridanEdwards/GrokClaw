#!/bin/sh
# Post a message to Slack.
# Usage:
#   slack-post.sh <channel> <message>
#   slack-post.sh <channel> <thread-ts> <message>
#   echo "text" | slack-post.sh <channel>
#   echo "text" | slack-post.sh <channel> <thread-ts>
set -eu

SLACK_BOT_TOKEN="xoxb-9365256667362-10728703443568-8NQZqo8Ha88s91LiTnj16EOY"

if [ "$#" -lt 1 ]; then
  echo "usage: slack-post.sh <channel> [thread-ts] [message]" >&2
  exit 1
fi

CHANNEL="$1"; shift

THREAD_TS=""
if [ "$#" -gt 0 ] && echo "$1" | grep -qE '^[0-9]+\.[0-9]+$'; then
  THREAD_TS="$1"; shift
fi

if [ "$#" -gt 0 ]; then
  MESSAGE="$*"
else
  MESSAGE=$(cat)
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/_slack_post.py" \
  "$SLACK_BOT_TOKEN" "$CHANNEL" "$THREAD_TS" "$MESSAGE"

#!/bin/sh
# Post a message to Slack.
# Usage:
#   slack-post.sh <channel> <message>
#   slack-post.sh <channel> <thread-ts> <message>
#   echo "text" | slack-post.sh <channel>
#   echo "text" | slack-post.sh <channel> <thread-ts>
# Env:   WORKSPACE_ROOT — workspace root (default: derived from script path)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

# Token from .env or fallback (for backwards compatibility)
if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi
SLACK_BOT_TOKEN="${SLACK_BOT_TOKEN:-xoxb-9365256667362-10728703443568-8NQZqo8Ha88s91LiTnj16EOY}"

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

python3 "$WORKSPACE_ROOT/tools/_slack_post.py" \
  "$SLACK_BOT_TOKEN" "$CHANNEL" "$THREAD_TS" "$MESSAGE"

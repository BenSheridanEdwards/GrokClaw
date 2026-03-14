#!/bin/sh
# Post a message to a Slack channel via the bot token.
# Usage: slack-post.sh <channel-id> <message>
#        slack-post.sh <channel-id> <thread-ts> <message>
set -eu

if [ -f "/Users/jarvis/.picoclaw/workspace/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . /Users/jarvis/.picoclaw/workspace/.env
  set +a
fi

SLACK_BOT_TOKEN="${SLACK_BOT_TOKEN:-xoxb-9365256667362-10728703443568-8NQZqo8Ha88s91LiTnj16EOY}"

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <channel-id> <message>" >&2
  echo "       $0 <channel-id> <thread-ts> <message>" >&2
  exit 1
fi

CHANNEL="$1"
shift

# If second arg looks like a Slack timestamp (digits.digits), treat as thread_ts
THREAD_TS=""
if echo "$1" | grep -qE '^[0-9]+\.[0-9]+$'; then
  THREAD_TS="$1"
  shift
fi

MESSAGE="$*"

payload=$(python3 -c "
import json, sys
d = {'channel': sys.argv[1], 'text': sys.argv[2]}
if sys.argv[3]:
    d['thread_ts'] = sys.argv[3]
print(json.dumps(d))
" "$CHANNEL" "$MESSAGE" "$THREAD_TS")

response=$(curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$payload")

ok=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ok'))")
if [ "$ok" != "True" ]; then
  echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); raise SystemExit(d.get('error','slack post failed'))" >&2
  exit 1
fi

echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ts',''))"

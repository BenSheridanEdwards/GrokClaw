#!/usr/bin/env python3
"""Post a message to a Telegram group topic via Bot API."""
import json, os, sys, urllib.request

token, chat_id, thread_id, message = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

# Default plain text: agent-generated copy often contains $1,234-style prices and underscores
# that break legacy Markdown. Set TELEGRAM_PARSE_MODE=Markdown (or HTML) to opt in.
payload = {"chat_id": int(chat_id), "text": message}
parse_mode = (os.environ.get("TELEGRAM_PARSE_MODE") or "").strip()
if parse_mode:
    payload["parse_mode"] = parse_mode
if thread_id:
    payload["message_thread_id"] = int(thread_id)

req = urllib.request.Request(
    f"https://api.telegram.org/bot{token}/sendMessage",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    data = json.load(resp)

if not data.get("ok"):
    print(f"ERROR: {data.get('description', 'unknown')}", file=sys.stderr)
    sys.exit(1)

print(data["result"]["message_id"])

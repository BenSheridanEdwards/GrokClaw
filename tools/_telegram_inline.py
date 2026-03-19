#!/usr/bin/env python3
"""Send Telegram message with inline keyboard buttons."""
import json
import sys
import urllib.request


token, chat_id, thread_id, message, button_json = sys.argv[1:6]
buttons = json.loads(button_json)

payload = {
    "chat_id": int(chat_id),
    "text": message,
    "reply_markup": {"inline_keyboard": [buttons]},
    "parse_mode": "Markdown",
}
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

result = data.get("result", {})
print(f"{result.get('message_id','')}:{result.get('chat',{}).get('id','')}")

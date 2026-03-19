#!/usr/bin/env python3
"""Send Telegram message with single-poller action buttons.

This uses InlineKeyboardMarkup with switch_inline_query_current_chat.
Tap inserts the action token into the current chat composer; user sends it
as a normal message. That keeps a single poller (OpenClaw only).
"""
import json
import sys
import urllib.request


def button_display_label(button: dict) -> str:
    """Label shown on the button (clean, no token)."""
    return str(button.get("text", "")).strip() or str(button.get("callback_data", "")).strip()


def action_token(button: dict) -> str:
    action = str(button.get("callback_data", "")).strip()
    if action:
        return action
    return str(button.get("text", "")).strip()


args = sys.argv[1:]
token, chat_id, thread_id, message, button_json = args[0], args[1], args[2], args[3], args[4]
parse_mode = args[5] if len(args) > 5 else "Markdown"

raw_buttons = json.loads(button_json)
buttons = []
for button in raw_buttons:
    label = button_display_label(button)
    token_value = action_token(button)
    if label and token_value:
        buttons.append((label, token_value))

if not buttons:
    print("ERROR: button-json produced no buttons", file=sys.stderr)
    sys.exit(1)

keyboard = [
    [{"text": label, "switch_inline_query_current_chat": token_value}]
    for (label, token_value) in buttons
]

payload = {
    "chat_id": int(chat_id),
    "text": message,
    "reply_markup": {"inline_keyboard": keyboard},
}
if parse_mode and parse_mode != "plain":
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

result = data.get("result", {})
print(f"{result.get('message_id','')}:{result.get('chat',{}).get('id','')}")

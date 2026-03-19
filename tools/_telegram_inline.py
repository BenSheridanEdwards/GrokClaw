#!/usr/bin/env python3
"""Send Telegram message with single-poller action buttons.

This uses InlineKeyboardMarkup with switch_inline_query_current_chat.
Tap inserts the action token into the current chat composer; user sends it
as a normal message. That keeps a single poller (OpenClaw only).
"""
import json
import sys
import urllib.request


_ACTION_LABELS = {
    "approve_idea": "Approve",
    "approve": "Approve",
    "merge": "Merge",
    "reject": "Reject",
}


def _action_to_label(action: str) -> str:
    """Derive a short label from action token prefix (e.g. approve_idea:12:GRO-21 -> Approve)."""
    prefix = (action.split(":")[0].lower() if action else "").strip()
    if not prefix:
        return "Action"
    return _ACTION_LABELS.get(prefix, prefix.replace("_", " ").title())


def button_label(button: dict) -> str:
    """Return clean user-facing label only. Callback data is never shown."""
    label = str(button.get("text", "")).strip()
    if label:
        return label
    action = str(button.get("callback_data", "")).strip()
    return _action_to_label(action) if action else ""


def action_token(button: dict) -> str:
    action = str(button.get("callback_data", "")).strip()
    if action:
        return action
    return str(button.get("text", "")).strip()


def build_keyboard(button_json: str) -> list:
    """Parse button-json and return compact inline_keyboard (one row, clean labels)."""
    raw_buttons = json.loads(button_json)
    normalized = []
    for button in raw_buttons:
        label = button_label(button)
        token_value = action_token(button)
        if label and token_value:
            normalized.append((label, token_value))
    if not normalized:
        return []
    return [
        [
            {"text": label, "switch_inline_query_current_chat": token_value}
            for (label, token_value) in normalized
        ]
    ]


def main() -> None:
    token, chat_id, thread_id, message, button_json = sys.argv[1:6]
    keyboard = build_keyboard(button_json)
    if not keyboard:
        print("ERROR: button-json produced no buttons", file=sys.stderr)
        sys.exit(1)

    payload = {
        "chat_id": int(chat_id),
        "text": message,
        "reply_markup": {"inline_keyboard": keyboard},
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


if __name__ == "__main__":
    main()

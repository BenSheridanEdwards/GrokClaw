#!/usr/bin/env python3
"""Post a message to a Telegram group topic via Bot API."""

from __future__ import annotations

import json
import os
import sys
import urllib.request


DEFAULT_TIMEOUT_SECONDS = 10
# https://core.telegram.org/bots/api#sendmessage
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
TRUNCATION_SUFFIX = "\n\n[truncated: Telegram sendMessage limit 4096 chars]"


def truncate_for_telegram(message: str, max_len: int = TELEGRAM_MAX_MESSAGE_LENGTH) -> str:
    if len(message) <= max_len:
        return message
    budget = max_len - len(TRUNCATION_SUFFIX)
    if budget < 1:
        return TRUNCATION_SUFFIX.strip()
    return message[:budget].rstrip() + TRUNCATION_SUFFIX


def build_payload(chat_id: str, thread_id: str, message: str) -> dict:
    # Default plain text: agent-generated copy often contains $1,234-style prices and underscores
    # that break legacy Markdown. Set TELEGRAM_PARSE_MODE=Markdown (or HTML) to opt in.
    payload = {"chat_id": int(chat_id), "text": message}
    parse_mode = (os.environ.get("TELEGRAM_PARSE_MODE") or "").strip()
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if thread_id:
        payload["message_thread_id"] = int(thread_id)
    return payload


def request_timeout_seconds() -> int:
    raw = (os.environ.get("TELEGRAM_API_TIMEOUT_SECONDS") or "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        timeout = int(raw)
    except ValueError as exc:  # pragma: no cover - defensive, exercised via caller usage
        raise SystemExit(f"Invalid TELEGRAM_API_TIMEOUT_SECONDS: {raw}") from exc
    if timeout <= 0:
        raise SystemExit("TELEGRAM_API_TIMEOUT_SECONDS must be positive")
    return timeout


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 4:
        print("usage: _telegram_post.py <token> <chat_id> <thread_id> <message>", file=sys.stderr)
        return 1

    token, chat_id, thread_id, message = argv
    message = truncate_for_telegram(message)
    payload = build_payload(chat_id, thread_id, message)
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=request_timeout_seconds()) as resp:
        data = json.load(resp)

    if not data.get("ok"):
        print(f"ERROR: {data.get('description', 'unknown')}", file=sys.stderr)
        return 1

    print(data["result"]["message_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

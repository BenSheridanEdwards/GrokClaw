#!/usr/bin/env python3
"""Poll Telegram callback_query updates and execute deterministic actions."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/Users/jarvis/Engineering/Projects/GrokClaw"))
ENV_PATH = WORKSPACE_ROOT / ".env"
STATE_DIR = WORKSPACE_ROOT / ".state"
OFFSET_PATH = STATE_DIR / "telegram-callback-offset.txt"


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def tg_request(token: str, method: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data


def answer_callback(token: str, callback_id: str, text: str) -> None:
    tg_request(token, "answerCallbackQuery", {"callback_query_id": callback_id, "text": text})


def edit_message(token: str, chat_id: int, message_id: int, text: str) -> None:
    tg_request(
        token,
        "editMessageText",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "Markdown",
        },
    )


def run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout.strip()


def handle_action(token: str, callback: dict, data: str) -> None:
    callback_id = callback["id"]
    msg = callback.get("message") or {}
    chat = msg.get("chat") or {}
    chat_id = int(chat.get("id", 0))
    message_id = int(msg.get("message_id", 0))

    parts = data.split(":")
    if len(parts) != 3:
        answer_callback(token, callback_id, "Invalid action payload")
        return

    action, pr_num, issue_id = parts
    answer_callback(token, callback_id, "Processing...")

    if action == "merge":
        code, out = run_cmd(
            ["gh", "pr", "merge", pr_num, "--squash", "--delete-branch", "--repo", "BenSheridanEdwards/GrokClaw"],
            WORKSPACE_ROOT,
        )
        if code == 0:
            run_cmd(["./tools/linear-transition.sh", issue_id, "Done"], WORKSPACE_ROOT)
            edit_message(token, chat_id, message_id, f"✅ Merged PR #{pr_num} and moved {issue_id} to Done.")
        else:
            edit_message(token, chat_id, message_id, f"❌ Merge failed for PR #{pr_num}.\n\n```\n{out[:2500]}\n```")
        return

    if action == "reject":
        code, out = run_cmd(
            [
                "gh",
                "pr",
                "comment",
                pr_num,
                "--repo",
                "BenSheridanEdwards/GrokClaw",
                "--body",
                "@cursor Changes requested by Ben from Telegram inline review. Please revise and mark ready again.",
            ],
            WORKSPACE_ROOT,
        )
        if code == 0:
            edit_message(token, chat_id, message_id, f"🛠️ Revisions requested for PR #{pr_num}.")
        else:
            edit_message(token, chat_id, message_id, f"❌ Failed to request revisions for PR #{pr_num}.\n\n```\n{out[:2500]}\n```")
        return

    if action == "approve_idea":
        code, out = run_cmd(["./tools/linear-transition.sh", issue_id, "In Progress"], WORKSPACE_ROOT)
        if code == 0:
            edit_message(token, chat_id, message_id, f"✅ Idea approved. {issue_id} is now In Progress.")
        else:
            edit_message(token, chat_id, message_id, f"❌ Failed to transition {issue_id}.\n\n```\n{out[:2500]}\n```")
        return

    answer_callback(token, callback_id, "Unknown action")


def main() -> int:
    env = load_env(ENV_PATH)
    token = env.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN missing", file=sys.stderr)
        return 1

    STATE_DIR.mkdir(parents=True, exist_ok=True)

    offset = 0
    if OFFSET_PATH.exists():
        try:
            offset = int(OFFSET_PATH.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            offset = 0

    while True:
        payload = {
            "offset": offset,
            "timeout": 30,
            "allowed_updates": ["callback_query"],
        }
        try:
            data = tg_request(token, "getUpdates", payload)
        except (urllib.error.URLError, TimeoutError):
            time.sleep(2)
            continue

        if not data.get("ok"):
            time.sleep(2)
            continue

        for item in data.get("result", []):
            update_id = int(item.get("update_id", 0))
            offset = max(offset, update_id + 1)
            OFFSET_PATH.write_text(str(offset), encoding="utf-8")

            callback = item.get("callback_query")
            if not callback:
                continue
            callback_data = callback.get("data", "")
            try:
                handle_action(token, callback, callback_data)
            except Exception as exc:  # keep daemon alive
                callback_id = callback.get("id")
                if callback_id:
                    try:
                        answer_callback(token, callback_id, "Action failed")
                    except Exception:
                        pass
                print(f"callback handler error: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())

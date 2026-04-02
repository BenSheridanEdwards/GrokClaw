#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path


def utc_now() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def workspace_root() -> Path:
    return Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[1]))


def state_file() -> Path:
    override = os.environ.get("WORKFLOW_HEALTH_STATE_FILE")
    if override:
        return Path(override)
    return Path.home() / ".openclaw" / "state" / "workflow-health-failures.json"


def read_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def post_health_alert(root: Path, message: str) -> None:
    subprocess.run(
        [str(root / "tools" / "telegram-post.sh"), "health", message],
        check=True,
        capture_output=True,
        text=True,
    )


def request_draft(root: Path, payload: dict) -> None:
    draft = payload["draft"]
    subprocess.run(
        [
            str(root / "tools" / "linear-draft-approval.sh"),
            "request",
            draft["id"],
            "suggestion",
            payload["failureHash"],
            "suggestions",
            draft["title"],
            draft["description"],
            "In Progress",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> int:
    payload = json.load(sys.stdin)
    root = workspace_root()
    state_path = state_file()
    state = read_state(state_path)
    now = utc_now()

    if payload.get("healthy"):
        if state:
            state["status"] = "resolved"
            state["last_seen"] = now
            write_state(state_path, state)
        return 0

    failure_hash = payload.get("failureHash", "")
    if state.get("hash") == failure_hash and state.get("status") == "open":
        return 0

    post_health_alert(root, payload["alertMessage"])
    if payload.get("draft"):
        request_draft(root, payload)

    next_state = {
        "hash": failure_hash,
        "first_seen": state.get("first_seen", now) if state.get("hash") == failure_hash else now,
        "last_seen": now,
        "status": "open",
    }
    write_state(state_path, next_state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

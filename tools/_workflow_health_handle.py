#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

LINEAR_TEAM_ID = "3f1b1054-07c6-4aad-a02c-89c78a43946b"
TERMINAL_LINEAR_STATES = {"done", "canceled", "cancelled", "duplicate", "completed"}


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


def post_health_alert(root: Path, message: str, buttons: list[dict] | None = None) -> None:
    if buttons:
        button_json = json.dumps(buttons)
        subprocess.run(
            [str(root / "tools" / "telegram-inline.sh"), "health", message, button_json, "plain"],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
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


def _norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def has_matching_pending_draft(root: Path, draft_title: str) -> bool:
    pending_dir = root / "data"
    if not pending_dir.exists():
        return False

    target = _norm(draft_title)
    for path in pending_dir.glob("pending-linear-draft-*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if payload.get("flow") != "suggestion":
            continue
        if _norm(payload.get("title", "")) == target:
            return True
    return False


def has_matching_open_linear_issue(draft_title: str) -> bool:
    titles_file = os.environ.get("WORKFLOW_HEALTH_OPEN_LINEAR_TITLES_FILE")
    if titles_file:
        try:
            raw = json.loads(Path(titles_file).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            raw = []
        target = _norm(draft_title)
        return any(_norm(str(item)) == target for item in raw)

    api_key = os.environ.get("LINEAR_API_KEY", "").strip()
    if not api_key:
        return False

    query = """
query ExistingIssues($teamId: ID!, $title: String!) {
  issues(
    first: 25
    filter: {
      team: { id: { eq: $teamId } }
      title: { containsIgnoreCase: $title }
    }
  ) {
    nodes {
      title
      state { name }
    }
  }
}
"""
    request_payload = json.dumps(
        {
            "query": query,
            "variables": {
                "teamId": LINEAR_TEAM_ID,
                "title": draft_title,
            },
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=request_payload,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            result = json.load(response)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return False

    nodes = (result.get("data") or {}).get("issues", {}).get("nodes", [])
    target = _norm(draft_title)
    for node in nodes:
        if _norm(node.get("title", "")) != target:
            continue
        state_name = _norm((node.get("state") or {}).get("name", ""))
        if state_name and state_name not in TERMINAL_LINEAR_STATES:
            return True
    return False


def has_matching_open_pr(draft_title: str) -> bool:
    titles_file = os.environ.get("WORKFLOW_HEALTH_OPEN_PR_TITLES_FILE")
    if titles_file:
        try:
            raw = json.loads(Path(titles_file).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            raw = []
        target = _norm(draft_title)
        return any(_norm(str(item)) == target for item in raw)

    try:
        completed = subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--json", "title"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    if completed.returncode != 0:
        return False
    try:
        items = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError:
        return False

    target = _norm(draft_title)
    for item in items:
        if _norm(item.get("title", "")) == target:
            return True
    return False


def should_request_draft(root: Path, payload: dict) -> bool:
    draft = payload.get("draft") or {}
    title = draft.get("title", "")
    if not title:
        return False
    if has_matching_pending_draft(root, title):
        return False
    if has_matching_open_linear_issue(title):
        return False
    if has_matching_open_pr(title):
        return False
    return True


def structural_hash(failures: list[dict]) -> str:
    """Hash workflow+kind pairs, ignoring timestamps in messages.

    The old approach hashed full messages which contain shifting timestamps
    (e.g. "expected run at 08:00 UTC" vs "09:00 UTC"), defeating dedup and
    causing 30+ identical alerts per day.
    """
    import hashlib
    keys = sorted({(f["workflow"], f["kind"]) for f in failures})
    blob = json.dumps(keys, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def main() -> int:
    payload = json.load(sys.stdin)
    root = workspace_root()
    state_path = state_file()
    state = read_state(state_path)
    now = utc_now()
    today = now[:10]

    if payload.get("healthy"):
        if state:
            state["status"] = "resolved"
            state["last_seen"] = now
            write_state(state_path, state)
        return 0

    struct_hash = structural_hash(payload.get("failures", []))
    already_open = state.get("status") == "open" and state.get("structHash") == struct_hash
    already_posted_today = already_open and state.get("last_seen", "")[:10] == today

    if already_posted_today:
        return 0

    RERUNNABLE_KINDS = {"missing_run", "stale_run", "error_run", "missing_research",
                        "missing_agent_report", "missing_audit", "missing_paperclip", "open_paperclip"}
    failed_workflows = []
    for f in payload.get("failures", []):
        wf = f.get("workflow", "")
        if f.get("kind") in RERUNNABLE_KINDS and wf not in failed_workflows:
            failed_workflows.append(wf)

    buttons = [
        {"text": f"Rerun {wf}", "callback_data": f"rerun_workflow:{wf}"}
        for wf in failed_workflows[:4]
    ]

    post_health_alert(root, payload["alertMessage"], buttons=buttons or None)
    if payload.get("draft") and should_request_draft(root, payload):
        request_draft(root, payload)

    next_state = {
        "hash": payload.get("failureHash", ""),
        "structHash": struct_hash,
        "first_seen": state.get("first_seen", now) if already_open else now,
        "last_seen": now,
        "status": "open",
    }
    write_state(state_path, next_state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

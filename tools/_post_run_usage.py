#!/usr/bin/env python3
"""
Post agent-run token usage to Paperclip's /cost-events endpoint by reading
openclaw's on-disk session file. Called from cron-paperclip-lifecycle.sh finish.

Usage:
  _post_run_usage.py <agent-name> <issue-id>

Env:
  PAPERCLIP_COMPANY_ID  required
  PAPERCLIP_API_BASE    default http://127.0.0.1:3100
  OPENCLAW_HOME         default ~/.openclaw
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

API_BASE = os.environ.get("PAPERCLIP_API_BASE", "http://127.0.0.1:3100").rstrip("/")
OPENCLAW_HOME = Path(os.environ.get("OPENCLAW_HOME", str(Path.home() / ".openclaw")))
COMPANY_ID = os.environ.get("PAPERCLIP_COMPANY_ID")

MAX_ATTEMPTS = 10
RETRY_INTERVAL = 0.5


def normalize_url_key(name: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


def load_session(url_key: str, session_key: str, min_ended_at: float = 0) -> dict | None:
    path = OPENCLAW_HOME / "agents" / url_key / "sessions" / "sessions.json"
    for attempt in range(MAX_ATTEMPTS):
        try:
            data = json.loads(path.read_text())
            session = data.get(session_key)
            if isinstance(session, dict) and session.get("status") == "done":
                ended_at = session.get("endedAt", 0)
                if isinstance(ended_at, (int, float)) and ended_at >= min_ended_at:
                    return session
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        if attempt < MAX_ATTEMPTS - 1:
            time.sleep(RETRY_INTERVAL)
    return None


def post_cost_event(agent_id: str, session: dict, issue_id: str) -> bool:
    input_tokens = int(session.get("inputTokens") or 0)
    output_tokens = int(session.get("outputTokens") or 0)
    if input_tokens <= 0 and output_tokens <= 0:
        return False

    cost_usd = float(session.get("estimatedCostUsd") or 0)
    payload = {
        "agentId": agent_id,
        "issueId": issue_id,
        "provider": session.get("modelProvider") or "unknown",
        "model": session.get("model") or "unknown",
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
        "costCents": round(cost_usd * 100),
        "occurredAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    try:
        req = urllib.request.Request(
            f"{API_BASE}/api/companies/{COMPANY_ID}/cost-events",
            data=json.dumps(payload).encode(),
            method="POST",
            headers={"X-Paperclip-Local": "true", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            resp.read()
        return True
    except Exception as exc:
        print(f"_post_run_usage: POST failed: {exc}", file=sys.stderr)
        return False


def resolve_agent_id(agent_name: str) -> str | None:
    try:
        req = urllib.request.Request(
            f"{API_BASE}/api/companies/{COMPANY_ID}/agents",
            headers={"X-Paperclip-Local": "true", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            agents = json.loads(resp.read())
        for a in agents:
            if a.get("name", "").lower() == agent_name.lower():
                return a["id"]
    except Exception:
        pass
    return None


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: _post_run_usage.py <agent-name> <issue-id>", file=sys.stderr)
        return 2
    if not COMPANY_ID:
        print("_post_run_usage: PAPERCLIP_COMPANY_ID required", file=sys.stderr)
        return 2

    agent_name = sys.argv[1]
    issue_id = sys.argv[2]
    url_key = normalize_url_key(agent_name)
    session_key = f"agent:{url_key}:paperclip:issue:{issue_id}"

    agent_id = resolve_agent_id(agent_name)
    if not agent_id:
        print(f"_post_run_usage: agent '{agent_name}' not found", file=sys.stderr)
        return 1

    start_ms = time.time() * 1000 - 120_000
    session = load_session(url_key, session_key, min_ended_at=start_ms)
    if not session:
        print(f"_post_run_usage: no ready session for {session_key}", file=sys.stderr)
        return 0

    if post_cost_event(agent_id, session, issue_id):
        input_t = int(session.get("inputTokens") or 0)
        output_t = int(session.get("outputTokens") or 0)
        cost = float(session.get("estimatedCostUsd") or 0)
        print(f"_post_run_usage: posted {agent_name} in={input_t} out={output_t} cost=${cost:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

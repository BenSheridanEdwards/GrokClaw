#!/usr/bin/env python3
"""
One-shot backfill: for every paperclip heartbeat_run in the current month whose
usageJson is null, read the matching openclaw session from
~/.openclaw/agents/<urlKey>/sessions/sessions.json and POST a cost-event to
paperclip. This reconstructs month-to-date token/cost tracking after fixing the
openclaw_gateway usage-forwarding gap going forward.

Usage:
  PAPERCLIP_COMPANY_ID=... ./tools/_backfill_paperclip_cost_events.py [--dry-run]

Env:
  PAPERCLIP_COMPANY_ID  required
  PAPERCLIP_API_BASE    default http://127.0.0.1:3100
  OPENCLAW_HOME         default ~/.openclaw
  PAPERCLIP_BACKFILL_SINCE  ISO date, default: first of current month UTC
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_BASE = os.environ.get("PAPERCLIP_API_BASE", "http://127.0.0.1:3100").rstrip("/")
OPENCLAW_HOME = Path(os.environ.get("OPENCLAW_HOME", str(Path.home() / ".openclaw")))
COMPANY_ID = os.environ.get("PAPERCLIP_COMPANY_ID")
DRY_RUN = "--dry-run" in sys.argv


def api(method: str, path: str, body: dict | None = None) -> dict | list:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "X-Paperclip-Local": "true",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def normalize_url_key(name: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


def load_sessions(url_key: str) -> dict:
    path = OPENCLAW_HOME / "agents" / url_key / "sessions" / "sessions.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        print(f"WARN: failed to parse {path}: {exc}", file=sys.stderr)
        return {}


def resolve_session_key(url_key: str, adapter_config: dict, context_snapshot: dict | None) -> str | None:
    strategy = (adapter_config or {}).get("sessionKeyStrategy")
    if strategy == "issue":
        issue_id = (context_snapshot or {}).get("issueId")
        if not issue_id:
            return None
        return f"agent:{url_key}:paperclip:issue:{issue_id}"
    static_key = (adapter_config or {}).get("sessionKey")
    if static_key:
        return f"agent:{url_key}:{static_key}"
    return None


def extract_usage(session: dict) -> dict | None:
    if not isinstance(session, dict):
        return None
    if session.get("status") != "done":
        return None
    input_tokens = int(session.get("inputTokens") or 0)
    output_tokens = int(session.get("outputTokens") or 0)
    cached = int(session.get("cacheRead") or 0)
    if input_tokens <= 0 and output_tokens <= 0 and cached <= 0:
        return None
    cost_usd = float(session.get("estimatedCostUsd") or 0)
    return {
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
        "costCents": round(cost_usd * 100),
        "provider": session.get("modelProvider") or "unknown",
        "model": session.get("model") or "unknown",
    }


def month_start_iso() -> str:
    override = os.environ.get("PAPERCLIP_BACKFILL_SINCE")
    if override:
        return override
    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, 1, tzinfo=timezone.utc).isoformat()


def main() -> int:
    if not COMPANY_ID:
        print("ERROR: PAPERCLIP_COMPANY_ID required", file=sys.stderr)
        return 2

    agents = api("GET", f"/api/companies/{COMPANY_ID}/agents")
    if not isinstance(agents, list):
        print("ERROR: unexpected agents payload", file=sys.stderr)
        return 2
    agents_by_id = {a["id"]: a for a in agents}
    sessions_by_url_key = {
        normalize_url_key(a["name"]): load_sessions(normalize_url_key(a["name"]))
        for a in agents
    }

    since = month_start_iso()
    # Grab a generous window; sort-order is newest-first from the API
    runs_resp = api("GET", f"/api/companies/{COMPANY_ID}/heartbeat-runs?limit=500")
    runs = runs_resp if isinstance(runs_resp, list) else runs_resp.get("items", [])

    written = skipped_done = skipped_no_session = skipped_no_tokens = failed = 0
    for run in runs:
        finished_at = run.get("finishedAt")
        if not finished_at or finished_at < since:
            continue
        if run.get("usageJson") is not None:
            skipped_done += 1
            continue
        if run.get("status") != "succeeded":
            continue
        agent = agents_by_id.get(run.get("agentId"))
        if not agent:
            continue
        url_key = normalize_url_key(agent["name"])
        sessions = sessions_by_url_key.get(url_key) or {}
        key = resolve_session_key(url_key, agent.get("adapterConfig") or {}, run.get("contextSnapshot"))
        if not key or key not in sessions:
            skipped_no_session += 1
            continue
        usage = extract_usage(sessions[key])
        if not usage:
            skipped_no_tokens += 1
            continue

        payload = {
            "agentId": agent["id"],
            "provider": usage["provider"],
            "model": usage["model"],
            "inputTokens": usage["inputTokens"],
            "outputTokens": usage["outputTokens"],
            "costCents": usage["costCents"],
            "occurredAt": finished_at,
        }
        issue_id = (run.get("contextSnapshot") or {}).get("issueId")
        if issue_id:
            payload["issueId"] = issue_id
        if DRY_RUN:
            print(
                f"DRY {agent['name']:6s} run={run['id'][:8]} tok=({usage['inputTokens']},{usage['outputTokens']}) cents={usage['costCents']} model={usage['model']}"
            )
            written += 1
            continue
        try:
            api("POST", f"/api/companies/{COMPANY_ID}/cost-events", payload)
            written += 1
            print(
                f"OK  {agent['name']:6s} run={run['id'][:8]} tok=({usage['inputTokens']},{usage['outputTokens']}) cents={usage['costCents']}"
            )
        except Exception as exc:
            failed += 1
            print(f"ERR {agent['name']:6s} run={run['id'][:8]}: {exc}", file=sys.stderr)

    print(
        f"\nwritten={written} already_tracked={skipped_done} "
        f"no_session={skipped_no_session} no_tokens={skipped_no_tokens} failed={failed}"
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

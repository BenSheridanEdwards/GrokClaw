#!/usr/bin/env python3
"""
Validate and sync GrokClaw OpenClaw cron jobs.

OpenClaw maps legacy payload { deliver: false, channel, to } → delivery.mode "none",
which disables Telegram completion announcements. Most agentTurn jobs use
top-level delivery: { mode: announce, channel: telegram, to: <group> }.

Jobs that post their own short summary via tools/telegram-post.sh (e.g. alpha-polymarket)
may use mode "none" so the gateway does not try to send a multi-thousand-line completion
transcript (Telegram sendMessage max 4096 chars).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

LEGACY_DELIVERY_KEYS = frozenset(
    {"deliver", "channel", "to", "bestEffortDeliver", "provider"}
)
TELEGRAM_GROUP_PREFIX = "-100"
AGENT_TURN_KINDS = frozenset({"agentTurn", "agent_turn"})
# Cron completion announce disabled; workflow still posts to Telegram via telegram-post.sh
SELF_ANNOUNCE_DELIVERY_NONE_JOBS = frozenset({"alpha-polymarket"})


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, val = line.partition("=")
        if key and _ and key not in os.environ:
            os.environ[key] = val


def _expand_env(text: str) -> str:
    _load_dotenv()
    return re.sub(
        r"\$\{(\w+)\}",
        lambda m: os.environ.get(m.group(1), m.group(0)),
        text,
    )


def load_json(path: Path, *, expand: bool = False) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if expand:
        raw = _expand_env(raw)
    return json.loads(raw)


def ensure_cron_job_state_dicts(store: dict[str, Any]) -> None:
    """Mutate store so every job has ``state`` as a dict.

    OpenClaw's cron ``start()`` reads ``job.state.runningAtMs`` before other code
    initializes ``state``. Repo ``cron/jobs.json`` omits ``state``; merge only copies
    ``state`` when the previous runtime row had that key, so first-time IDs can be
    written without ``state`` and crash the scheduler. Legacy string ``state`` values
    are coerced to ``{}``.
    """
    jobs = store.get("jobs")
    if not isinstance(jobs, list):
        return
    for job in jobs:
        if not isinstance(job, dict):
            continue
        st = job.get("state")
        if isinstance(st, dict):
            continue
        job["state"] = {}


def validate_jobs(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        return ["jobs must be a non-empty array"]
    for job in jobs:
        if not isinstance(job, dict):
            errors.append("job entry must be an object")
            continue
        name = job.get("name", "?")
        payload = job.get("payload")
        if not isinstance(payload, dict):
            continue
        if payload.get("kind") not in AGENT_TURN_KINDS:
            continue
        legacy = [k for k in LEGACY_DELIVERY_KEYS if k in payload]
        if legacy:
            errors.append(
                f"{name}: remove legacy payload keys {legacy}; "
                "use top-level delivery (see docs/multi-agent-setup.md)"
            )
        delivery = job.get("delivery")
        if not isinstance(delivery, dict):
            errors.append(
                f"{name}: missing job-level delivery; "
                'use {"mode": "announce", "channel": "telegram", "to": "<group>", '
                '"bestEffort": true}'
            )
            continue
        mode = delivery.get("mode")
        if mode == "none":
            if name not in SELF_ANNOUNCE_DELIVERY_NONE_JOBS:
                errors.append(
                    f'{name}: delivery.mode "none" is only allowed for jobs that post their '
                    f"own Telegram summary ({', '.join(sorted(SELF_ANNOUNCE_DELIVERY_NONE_JOBS))})"
                )
            continue
        if mode != "announce":
            errors.append(
                f'{name}: delivery.mode must be "announce" or "none" (see cron-jobs-tool.py)'
            )
            continue
        if delivery.get("channel") != "telegram":
            errors.append(f'{name}: delivery.channel must be "telegram"')
        to_val = str(delivery.get("to", "")).strip()
        if not to_val.startswith(TELEGRAM_GROUP_PREFIX):
            errors.append(
                f"{name}: delivery.to must be your Telegram supergroup id (negative int string)"
            )
    return errors


def merge_runtime_fields(
    repo_jobs: dict[str, Any], target_path: Path
) -> dict[str, Any]:
    """Preserve OpenClaw scheduler state when syncing from git; include orphan old jobs.

    Orphan jobs (ids not present in the repo file) are kept only when their name does
    not collide with a repo job. Duplicate names caused double-scheduling and broken
    legacy rows (e.g. agentTurn without message) that crash the gateway scheduler.
    """
    if not target_path.is_file():
        ensure_cron_job_state_dicts(repo_jobs)
        return repo_jobs
    try:
        old = load_json(target_path)
    except (OSError, json.JSONDecodeError):
        ensure_cron_job_state_dicts(repo_jobs)
        return repo_jobs
    old_by_id = {
        j["id"]: j for j in old.get("jobs", []) if isinstance(j, dict) and "id" in j
    }
    repo_ids = {j["id"] for j in repo_jobs.get("jobs", []) if isinstance(j, dict)}
    repo_names = {
        j["name"]
        for j in repo_jobs.get("jobs", [])
        if isinstance(j, dict) and isinstance(j.get("name"), str)
    }
    out = dict(repo_jobs)
    merged: list[dict[str, Any]] = []
    for job in repo_jobs.get("jobs", []):
        if not isinstance(job, dict):
            merged.append(job)
            continue
        j = dict(job)
        oid = old_by_id.get(j.get("id", ""), "")
        if isinstance(oid, dict):
            if "state" in oid:
                j["state"] = oid["state"]
            for key in ("createdAtMs", "updatedAtMs"):
                if key in oid:
                    j[key] = oid[key]
        merged.append(j)
    for old_job in old.get("jobs", []):
        if not isinstance(old_job, dict) or old_job.get("id") in repo_ids:
            continue
        orphan_name = old_job.get("name")
        if isinstance(orphan_name, str) and orphan_name in repo_names:
            continue
        merged.append(old_job)
    out["jobs"] = merged
    ensure_cron_job_state_dicts(out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Cron jobs validate / sync")
    sub = parser.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Validate jobs.json")
    v.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Path to jobs.json (default: repo cron/jobs.json)",
    )

    s = sub.add_parser("sync", help="Merge into ~/.openclaw/cron/jobs.json and write")
    s.add_argument(
        "--repo",
        default=None,
        help="Repo jobs.json path (default: <workspace>/cron/jobs.json)",
    )
    s.add_argument(
        "--target",
        default=None,
        help="Target path (default: ~/.openclaw/cron/jobs.json)",
    )
    s.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only; do not write",
    )

    st = sub.add_parser("strip", help="Remove scheduler state from repo jobs.json")
    st.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Path to jobs.json (default: repo cron/jobs.json)",
    )

    args = parser.parse_args()
    workspace = Path(__file__).resolve().parents[1]

    if args.cmd == "strip":
        path = Path(args.path) if args.path else workspace / "cron" / "jobs.json"
        try:
            data = load_json(path)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"cron-jobs-tool: {e}", file=sys.stderr)
            return 2
        scheduler_keys = {"state", "createdAtMs", "updatedAtMs"}
        changed = False
        for job in data.get("jobs", []):
            for k in scheduler_keys:
                if k in job:
                    del job[k]
                    changed = True
        if not changed:
            print(f"cron-jobs-tool strip: already clean ({path})")
            return 0
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"cron-jobs-tool strip: removed scheduler state from {path}")
        return 0

    if args.cmd == "validate":
        path = Path(args.path) if args.path else workspace / "cron" / "jobs.json"
        try:
            data = load_json(path, expand=True)
        except FileNotFoundError:
            print(f"cron-jobs-tool: not found: {path}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as e:
            print(f"cron-jobs-tool: invalid JSON in {path}: {e}", file=sys.stderr)
            return 2
        errs = validate_jobs(data)
        if errs:
            print("cron-jobs-tool validate: FAILED", file=sys.stderr)
            for e in errs:
                print(f"  {e}", file=sys.stderr)
            return 1
        print(f"cron-jobs-tool validate: OK ({path})")
        return 0

    repo_path = Path(args.repo) if args.repo else workspace / "cron" / "jobs.json"
    target = (
        Path(args.target).expanduser()
        if args.target
        else Path.home() / ".openclaw" / "cron" / "jobs.json"
    )

    try:
        data = load_json(repo_path, expand=True)
    except FileNotFoundError:
        print(f"cron-jobs-tool: not found: {repo_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"cron-jobs-tool: invalid JSON in {repo_path}: {e}", file=sys.stderr)
        return 2

    errs = validate_jobs(data)
    if errs:
        print("cron-jobs-tool sync: validation FAILED", file=sys.stderr)
        for e in errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    merged = merge_runtime_fields(data, target)
    if args.dry_run:
        print(f"cron-jobs-tool sync: dry-run OK → would write {target}")
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    print(f"cron-jobs-tool sync: wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

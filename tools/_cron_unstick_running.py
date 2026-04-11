#!/usr/bin/env python3
"""Normalize ~/.openclaw/cron/jobs.json for a healthy OpenClaw cron scheduler.

1. Ensure every job has a dict `state` (OpenClaw's cron `start()` reads
   `job.state.runningAtMs` before other code paths initialize `state`; a missing
   `state` crashes the whole scheduler with:
   TypeError: Cannot read properties of undefined (reading 'runningAtMs').
2. Remove stale `runningAtMs` (zombie in-flight). OpenClaw refuses `cron run`
   with \"already-running\" while this field is set.

After changes, restart the gateway (e.g. ./tools/gateway-ctl.sh restart).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def default_cron_path() -> Path:
    override = os.environ.get("OPENCLAW_CRON_JOBS_PATH", "").strip()
    if override:
        return Path(override)
    return Path.home() / ".openclaw" / "cron" / "jobs.json"


def ensure_job_state_dicts(data: dict) -> tuple[int, list[str]]:
    """Ensure each job has ``state: {}`` when missing or not a dict. Returns (fixed_count, names)."""
    fixed = 0
    names: list[str] = []
    for job in data.get("jobs", []):
        if not isinstance(job, dict):
            continue
        st = job.get("state")
        if isinstance(st, dict):
            continue
        job["state"] = {}
        fixed += 1
        n = job.get("name")
        names.append(str(n) if n else job.get("id", "?"))
    return fixed, names


def strip_running_at_ms(data: dict) -> tuple[int, list[str]]:
    """Return (count_removed, job_names_touched)."""
    removed = 0
    names: list[str] = []
    for job in data.get("jobs", []):
        if not isinstance(job, dict):
            continue
        st = job.get("state")
        if not isinstance(st, dict):
            continue
        if "runningAtMs" in st:
            del st["runningAtMs"]
            removed += 1
            n = job.get("name")
            names.append(str(n) if n else job.get("id", "?"))
    return removed, names


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Normalize OpenClaw cron jobs.json (state dict + clear runningAtMs)"
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Path to jobs.json (default: ~/.openclaw/cron/jobs.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing",
    )
    args = parser.parse_args(argv)
    path = Path(args.path) if args.path else default_cron_path()
    if not path.is_file():
        print(f"cron-unstick: missing {path}", file=sys.stderr)
        return 1
    data = json.loads(path.read_text(encoding="utf-8"))
    fixed, state_names = ensure_job_state_dicts(data)
    if fixed:
        print(
            f"cron-unstick: ensured state object on {fixed} job(s): {', '.join(state_names)}"
        )
    removed, run_names = strip_running_at_ms(data)
    if removed:
        print(f"cron-unstick: clearing runningAtMs on {removed} job(s): {', '.join(run_names)}")
    if fixed == 0 and removed == 0:
        print("cron-unstick: no changes needed")
        return 0
    if args.dry_run:
        return 0
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"cron-unstick: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

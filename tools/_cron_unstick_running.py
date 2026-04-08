#!/usr/bin/env python3
"""Remove stale `runningAtMs` from ~/.openclaw/cron/jobs.json (zombie in-flight cron).

OpenClaw refuses `openclaw cron run` with reason \"already-running\" while this field
is set. After a crash or dropped client, clear it and restart the gateway.
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
    parser = argparse.ArgumentParser(description="Strip runningAtMs from OpenClaw cron jobs.json")
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
    removed, names = strip_running_at_ms(data)
    if removed == 0:
        print("cron-unstick: no runningAtMs fields found")
        return 0
    print(f"cron-unstick: clearing runningAtMs on {removed} job(s): {', '.join(names)}")
    if args.dry_run:
        return 0
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"cron-unstick: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

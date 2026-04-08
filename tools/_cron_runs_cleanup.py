#!/usr/bin/env python3
"""Remove bad lines from data/cron-runs/*.jsonl.

1. Same-job duplicate \"started\" rows without a terminal between them (keep the last).
2. Globally latest row per job is \"started\" and older than grace_hours (orphaned run).

Dry-run by default; pass --apply to rewrite files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path


def workspace_root() -> Path:
    return Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[1]))


def parse_ts(raw: str | None) -> dt.datetime | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return dt.datetime.strptime(raw, fmt).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    return None


TERMINAL = frozenset({"ok", "error", "skipped"})


@dataclass(frozen=True)
class LineAction:
    path: Path
    line_index: int
    reason: str
    job: str


def _iter_jsonl_records(cron_dir: Path) -> list[tuple[Path, int, dict]]:
    out: list[tuple[Path, int, dict]] = []
    if not cron_dir.is_dir():
        return out
    for path in sorted(cron_dir.glob("*.jsonl")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and obj.get("job"):
                out.append((path, idx, obj))
    return out


def redundant_started_indices_for_file(lines: list[str]) -> set[int]:
    """Drop earlier same-job \"started\" when another \"started\" follows before terminal."""
    to_drop: set[int] = set()
    last_started: dict[str, int | None] = {}
    for idx, raw in enumerate(lines):
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        job = obj.get("job")
        st = obj.get("status")
        if not isinstance(job, str) or not isinstance(st, str):
            continue
        if st == "started":
            prev = last_started.get(job)
            if prev is not None:
                to_drop.add(prev)
            last_started[job] = idx
        elif st in TERMINAL:
            last_started[job] = None
    return to_drop


def _to_naive_utc(ts: dt.datetime) -> dt.datetime:
    if ts.tzinfo:
        return ts.astimezone(dt.timezone.utc).replace(tzinfo=None)
    return ts


def orphan_started_indices(
    records: list[tuple[Path, int, dict]],
    now: dt.datetime,
    grace_hours: float,
) -> set[tuple[Path, int]]:
    """Latest record per job (any status) is \"started\" and older than grace."""
    best: dict[str, tuple[dt.datetime, Path, int, str]] = {}
    for path, idx, obj in records:
        job = obj.get("job")
        st = obj.get("status")
        ts_raw = obj.get("ts")
        if not isinstance(job, str) or not isinstance(st, str):
            continue
        ts = parse_ts(ts_raw if isinstance(ts_raw, str) else None)
        if not ts:
            continue
        cur = best.get(job)
        if cur is None or ts > cur[0]:
            best[job] = (ts, path, idx, st)

    out: set[tuple[Path, int]] = set()
    grace = dt.timedelta(hours=grace_hours)
    naive_now = _to_naive_utc(now)
    for _job, (ts, path, idx, st) in best.items():
        if st != "started":
            continue
        if naive_now - _to_naive_utc(ts) > grace:
            out.add((path, idx))
    return out


def plan_cleanup(
    root: Path,
    *,
    now: dt.datetime,
    grace_hours: float,
) -> list[LineAction]:
    cron_dir = root / "data" / "cron-runs"
    actions: list[LineAction] = []
    seen: set[tuple[Path, int]] = set()

    if not cron_dir.is_dir():
        return actions

    records = _iter_jsonl_records(cron_dir)

    for path in sorted(cron_dir.glob("*.jsonl")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for idx in redundant_started_indices_for_file(lines):
            key = (path, idx)
            if key in seen:
                continue
            seen.add(key)
            job = ""
            if idx < len(lines):
                try:
                    job = str(json.loads(lines[idx]).get("job", ""))
                except (json.JSONDecodeError, TypeError):
                    pass
            actions.append(LineAction(path, idx, "duplicate_started", job))

    for path, idx in orphan_started_indices(records, now, grace_hours):
        key = (path, idx)
        if key in seen:
            continue
        seen.add(key)
        job = ""
        for p, i, o in records:
            if p == path and i == idx:
                job = str(o.get("job", ""))
                break
        actions.append(LineAction(path, idx, "orphan_started", job))

    actions.sort(key=lambda a: (str(a.path), -a.line_index))
    return actions


def apply_line_removals(actions: list[LineAction]) -> None:
    by_file: dict[Path, set[int]] = {}
    for a in actions:
        by_file.setdefault(a.path, set()).add(a.line_index)

    for path, drop in by_file.items():
        lines = path.read_text(encoding="utf-8").splitlines()
        new_lines = [ln for i, ln in enumerate(lines) if i not in drop]
        text = "\n".join(new_lines)
        if new_lines:
            text += "\n"
        path.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Clean data/cron-runs/*.jsonl")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Rewrite files (default is dry-run)",
    )
    parser.add_argument(
        "--grace-hours",
        type=float,
        default=2.0,
        help="Orphan \"started\" must be older than this (default: 2)",
    )
    parser.add_argument(
        "--now",
        default=None,
        help="UTC instant for tests (format 2026-04-07T20:00:00Z)",
    )
    args = parser.parse_args(argv)
    root = workspace_root()

    if args.now:
        now = parse_ts(args.now)
        if not now:
            print("cron-runs-cleanup: invalid --now", file=sys.stderr)
            return 1
    else:
        now = dt.datetime.now(dt.timezone.utc)

    actions = plan_cleanup(root, now=now, grace_hours=args.grace_hours)
    for a in actions:
        try:
            rel = a.path.relative_to(root)
        except ValueError:
            rel = a.path
        print(f"{rel}:{a.line_index + 1} job={a.job!r} {a.reason}")

    if not actions:
        print("cron-runs-cleanup: nothing to do")
        return 0

    if args.apply:
        apply_line_removals(actions)
        print(f"cron-runs-cleanup: removed {len(actions)} line(s)")
    else:
        print(f"cron-runs-cleanup: dry-run ({len(actions)} line(s)); use --apply to write")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

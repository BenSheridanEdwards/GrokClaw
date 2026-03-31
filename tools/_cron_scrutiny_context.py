#!/usr/bin/env python3
"""
Emit context for Grok cron scrutiny: run stats + recent JSONL + simple gap hints.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

AGENT_TURN_KINDS = frozenset({"agentTurn", "agent_turn"})


def parse_ts(ts: str) -> datetime | None:
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def load_jsonl_paths(workspace: Path) -> list[Path]:
    base = workspace / "data" / "cron-runs"
    if not base.is_dir():
        return []
    days = [
        (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(0, 4)
    ]
    paths = []
    for d in days:
        p = base / f"{d}.jsonl"
        if p.is_file():
            paths.append(p)
    return paths


def read_records(paths: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for p in paths:
        text = p.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def load_registered_jobs(workspace: Path) -> list[str]:
    p = workspace / "cron" / "jobs.json"
    if not p.is_file():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    names = []
    for j in data.get("jobs", []):
        if not isinstance(j, dict) or not j.get("enabled", True):
            continue
        pl = j.get("payload") or {}
        if pl.get("kind") not in AGENT_TURN_KINDS:
            continue
        n = j.get("name")
        if isinstance(n, str) and n:
            names.append(n)
    return names


def main() -> int:
    workspace = Path(__file__).resolve().parents[1]
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=36)

    paths = load_jsonl_paths(workspace)
    records = read_records(paths)
    registered = load_registered_jobs(workspace)

    recent: list[dict] = []
    for r in records:
        ts = parse_ts(str(r.get("ts", "")))
        if ts is None:
            continue
        if ts.replace(tzinfo=timezone.utc) >= cutoff:
            recent.append(r)

    by_job: dict[str, list[dict]] = defaultdict(list)
    for r in recent:
        jn = r.get("job")
        if isinstance(jn, str):
            by_job[jn].append(r)

    print("=== registered_agent_turn_jobs ===")
    for n in registered:
        print(n)
    print()

    print("=== run_stats_last_36h_utc ===")
    for job in sorted(by_job.keys()):
        runs = sorted(
            by_job[job],
            key=lambda x: parse_ts(str(x.get("ts", ""))) or datetime.min.replace(tzinfo=timezone.utc),
        )
        last = runs[-1]
        summaries = [str(r.get("summary", "")).strip() for r in runs]
        lens = [len(s) for s in summaries if s]
        empty = sum(1 for s in summaries if not s)
        c = Counter(summaries)
        most_common = c.most_common(1)[0] if c else ("", 0)
        dup_hint = ""
        if most_common[1] >= 3 and len(most_common[0]) > 10:
            dup_hint = f" identical_summary_x{most_common[1]}"
        avg_part = f"avg_len={sum(lens) / len(lens):.0f}" if lens else "avg_len=n/a"
        print(
            f"{job}: count={len(runs)} last_ts={last.get('ts')} "
            f"status={last.get('status')} agent={last.get('agent')} "
            f"empty_summaries={empty} {avg_part}{dup_hint}"
        )
    if not by_job:
        print("(no records in last 36h — cron-run-record.sh may not be wired yet)")
    print()

    print("=== jobs_enabled_but_no_records_36h ===")
    for name in registered:
        if name == "grok-cron-scrutiny":
            continue
        if name not in by_job:
            print(name)
    print()

    print("=== recent_runs_tail_newest_last (max 100) ===")
    all_recent = sorted(
        recent,
        key=lambda x: parse_ts(str(x.get("ts", ""))) or datetime.min.replace(tzinfo=timezone.utc),
    )
    tail = all_recent[-100:]
    for r in tail:
        print(json.dumps(r, ensure_ascii=False))
    print("=== end ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

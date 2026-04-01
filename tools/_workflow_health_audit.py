#!/usr/bin/env python3
"""
Read-only audit: verify the four core cron workflows recorded a run near each
expected schedule fire time (data/cron-runs/*.jsonl).

Exit 0 if all checks pass, 1 if any expected window is missing a record.
Does not repair or call external services.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


UTC = timezone.utc


@dataclass(frozen=True)
class JobExpectation:
    name: str
    schedule_expr: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_iso_ts(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(UTC)


def _last_expected_fire(schedule_expr: str, now: datetime) -> datetime:
    """Return the most recent cron fire time (UTC) at or before `now` for supported exprs."""
    now = now.astimezone(UTC)
    if schedule_expr == "0 * * * *":
        return now.replace(minute=0, second=0, microsecond=0)
    if schedule_expr == "0 8 * * *":
        today_8 = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= today_8:
            return today_8
        prev = now - timedelta(days=1)
        return prev.replace(hour=8, minute=0, second=0, microsecond=0)
    if schedule_expr == "0 7,13,19 * * *":
        slots = (7, 13, 19)
        best: datetime | None = None
        for h in slots:
            t = now.replace(hour=h, minute=0, second=0, microsecond=0)
            if t <= now and (best is None or t > best):
                best = t
        if best is not None:
            return best
        prev = now - timedelta(days=1)
        return prev.replace(hour=19, minute=0, second=0, microsecond=0)
    raise ValueError(f"unsupported schedule expr: {schedule_expr!r}")


def _grace_for_schedule(schedule_expr: str) -> timedelta:
    if schedule_expr == "0 * * * *":
        return timedelta(minutes=75)
    return timedelta(minutes=120)


def _load_cron_jobs(repo: Path) -> dict[str, JobExpectation]:
    data = json.loads((repo / "cron" / "jobs.json").read_text(encoding="utf-8"))
    out: dict[str, JobExpectation] = {}
    for j in data.get("jobs", []):
        name = j.get("name")
        expr = (j.get("schedule") or {}).get("expr")
        if name and expr:
            out[str(name)] = JobExpectation(name=str(name), schedule_expr=str(expr))
    return out


def _read_jsonl_paths(repo: Path, day: datetime) -> list[Path]:
    dr = repo / "data" / "cron-runs"
    if not dr.is_dir():
        return []
    names = {day.strftime("%Y-%m-%d.jsonl")}
    prev = (day - timedelta(days=1)).strftime("%Y-%m-%d.jsonl")
    names.add(prev)
    return sorted(p for p in (dr / n for n in names) if p.is_file())


def _records_for_job(paths: list[Path], job: str) -> list[dict]:
    rows: list[dict] = []
    for p in paths:
        text = p.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("job") == job:
                rows.append(rec)
    return rows


def audit(now: datetime | None = None, repo: Path | None = None) -> tuple[list[str], list[str]]:
    repo = repo or _repo_root()
    now = now or datetime.now(tz=UTC)
    jobs = _load_cron_jobs(repo)
    core = (
        "grok-daily-brief",
        "grok-openclaw-research",
        "alpha-polymarket",
        "kimi-polymarket",
    )
    paths = _read_jsonl_paths(repo, now)

    ok_msgs: list[str] = []
    fail_msgs: list[str] = []

    for name in core:
        if name not in jobs:
            fail_msgs.append(f"{name}: not defined in cron/jobs.json")
            continue
        exp = jobs[name]
        try:
            expected = _last_expected_fire(exp.schedule_expr, now)
        except ValueError as e:
            fail_msgs.append(f"{name}: {e}")
            continue
        grace = _grace_for_schedule(exp.schedule_expr)
        window_end = expected + grace
        if now < expected:
            ok_msgs.append(f"{name}: no fire due yet (next at {expected.isoformat()})")
            continue

        recs = _records_for_job(paths, name)
        found = False
        for rec in recs:
            ts_raw = rec.get("ts")
            if not ts_raw:
                continue
            try:
                ts = _parse_iso_ts(str(ts_raw))
            except (TypeError, ValueError):
                continue
            if expected <= ts <= window_end:
                found = True
                break

        if found:
            ok_msgs.append(
                f"{name}: ok (expected fire {expected.isoformat()}, window +{grace})"
            )
        else:
            fail_msgs.append(
                f"{name}: no cron-run-record between {expected.isoformat()} "
                f"and {window_end.isoformat()} (now {now.isoformat()})"
            )

    return ok_msgs, fail_msgs


def main() -> int:
    failures_only = "--failures-only" in sys.argv
    ok_msgs, fail_msgs = audit(repo=_repo_root())
    if failures_only:
        for m in fail_msgs:
            print(m)
        return 1 if fail_msgs else 0
    for m in ok_msgs:
        print(m)
    for m in fail_msgs:
        print(m, file=sys.stderr)
    return 1 if fail_msgs else 0


if __name__ == "__main__":
    sys.exit(main())

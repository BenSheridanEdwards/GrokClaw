#!/usr/bin/env python3
"""Generate CTO baseline reliability and economics KPIs.

Sources:
- data/cron-runs/*.jsonl
- tools/_workflow_health.py (audit-quick + audit)
- Paperclip heartbeat run usage/cost payloads
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


CORE_WORKFLOWS: Dict[str, Dict[str, Any]] = {
    "grok-daily-brief": {
        "schedule": {"kind": "daily", "hours": (8,)},
        "grace_minutes": 20,
    },
    "grok-openclaw-research": {
        "schedule": {"kind": "daily", "hours": (7, 13, 19)},
        "grace_minutes": 20,
    },
    "alpha-polymarket": {
        "schedule": {"kind": "hourly", "minute": 0},
        "grace_minutes": 20,
    },
}

TERMINAL_STATUSES = {"ok", "error", "skipped"}


def workspace_root() -> Path:
    return Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[1]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CTO KPI report")
    parser.add_argument(
        "--date",
        default=dt.datetime.utcnow().strftime("%Y-%m-%d"),
        help="Anchor UTC date in YYYY-MM-DD format (default: today UTC)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Number of days ending at --date (default: 14)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON only",
    )
    parser.add_argument(
        "--paperclip-runs-file",
        default="",
        help="Optional JSON file with heartbeat run rows (for offline/test mode)",
    )
    parser.add_argument(
        "--paperclip-base-url",
        default=os.environ.get("PAPERCLIP_BASE_URL", "http://127.0.0.1:3100"),
        help="Paperclip base URL (default: http://127.0.0.1:3100)",
    )
    parser.add_argument(
        "--paperclip-company-id",
        default=os.environ.get("PAPERCLIP_COMPANY_ID", "2e003f55-4bdf-465b-acd3-143ce3745aa8"),
        help="Paperclip company UUID",
    )
    return parser.parse_args()


def parse_ts(raw: Optional[str]) -> Optional[dt.datetime]:
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return dt.datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def date_window(anchor: dt.date, days: int) -> Tuple[dt.datetime, dt.datetime, List[dt.date]]:
    safe_days = max(1, int(days))
    start_date = anchor - dt.timedelta(days=safe_days - 1)
    dates = [start_date + dt.timedelta(days=i) for i in range(safe_days)]
    start_dt = dt.datetime.combine(start_date, dt.time.min)
    end_dt = dt.datetime.combine(anchor, dt.time.max)
    return start_dt, end_dt, dates


def read_cron_records(root: Path, dates: List[dt.date]) -> List[dict]:
    out: List[dict] = []
    base = root / "data" / "cron-runs"
    for day in dates:
        path = base / f"{day.strftime('%Y-%m-%d')}.jsonl"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                out.append(item)
    return out


def scheduled_slots_for_workflow(
    meta: Dict[str, Any], start_dt: dt.datetime, end_dt: dt.datetime
) -> List[dt.datetime]:
    schedule = meta["schedule"]
    slots: List[dt.datetime] = []

    if schedule["kind"] == "hourly":
        minute = int(schedule.get("minute", 0))
        current = start_dt.replace(minute=minute, second=0, microsecond=0)
        if current < start_dt:
            current += dt.timedelta(hours=1)
        while current <= end_dt:
            slots.append(current)
            current += dt.timedelta(hours=1)
        return slots

    hours = sorted(int(hour) for hour in schedule["hours"])
    day = start_dt.date()
    end_day = end_dt.date()
    while day <= end_day:
        for hour in hours:
            candidate = dt.datetime.combine(day, dt.time(hour=hour, minute=0))
            if start_dt <= candidate <= end_dt:
                slots.append(candidate)
        day += dt.timedelta(days=1)
    return slots


def summarize_reliability(records: List[dict], start_dt: dt.datetime, end_dt: dt.datetime) -> dict:
    terminal_records: List[Tuple[dt.datetime, dict]] = []
    for record in records:
        ts = parse_ts(record.get("ts"))
        if not ts or ts < start_dt or ts > end_dt:
            continue
        status = str(record.get("status", "")).strip().lower()
        if status in TERMINAL_STATUSES:
            terminal_records.append((ts, record))

    status_counts = {"ok": 0, "error": 0, "skipped": 0, "started": 0}
    for _ts, record in terminal_records:
        st = str(record.get("status", "")).strip().lower()
        if st in status_counts:
            status_counts[st] += 1

    expected_slots = 0
    terminal_by_workflow: Dict[str, int] = {}
    workflow_summaries: Dict[str, dict] = {}
    for job, meta in CORE_WORKFLOWS.items():
        slots = scheduled_slots_for_workflow(meta, start_dt, end_dt)
        expected_slots += len(slots)
        per_job = [
            record
            for ts, record in terminal_records
            if str(record.get("job", "")) == job and ts >= start_dt and ts <= end_dt
        ]
        terminal_by_workflow[job] = len(per_job)
        ok = sum(1 for row in per_job if str(row.get("status", "")).lower() == "ok")
        err = sum(1 for row in per_job if str(row.get("status", "")).lower() == "error")
        skipped = sum(1 for row in per_job if str(row.get("status", "")).lower() == "skipped")
        adherence = (len(per_job) / len(slots) * 100.0) if slots else 100.0
        workflow_summaries[job] = {
            "expectedSlots": len(slots),
            "terminalRuns": len(per_job),
            "adherencePercent": round(adherence, 2),
            "ok": ok,
            "error": err,
            "skipped": skipped,
        }

    terminal_runs = len(terminal_records)
    adherence_percent = (terminal_runs / expected_slots * 100.0) if expected_slots > 0 else 100.0

    # MTTR approximation: for each error, measure to next ok/skipped on same workflow.
    errors: List[Tuple[dt.datetime, dict]] = [
        (ts, record)
        for ts, record in sorted(terminal_records, key=lambda item: item[0])
        if str(record.get("status", "")).lower() == "error"
    ]
    recoveries_minutes: List[float] = []
    unrecovered = 0
    for ts, record in errors:
        job = str(record.get("job", ""))
        next_recovery = next(
            (
                next_ts
                for next_ts, next_record in sorted(terminal_records, key=lambda item: item[0])
                if next_ts > ts
                and str(next_record.get("job", "")) == job
                and str(next_record.get("status", "")).lower() in {"ok", "skipped"}
            ),
            None,
        )
        if next_recovery is None:
            unrecovered += 1
            continue
        recoveries_minutes.append((next_recovery - ts).total_seconds() / 60.0)

    # Stuck in-progress: latest record for any workflow is started and older than grace.
    stuck_in_progress = 0
    all_by_workflow: Dict[str, Tuple[dt.datetime, dict]] = {}
    for record in records:
        ts = parse_ts(record.get("ts"))
        if not ts:
            continue
        job = str(record.get("job", ""))
        if job not in CORE_WORKFLOWS:
            continue
        current = all_by_workflow.get(job)
        if current is None or ts > current[0]:
            all_by_workflow[job] = (ts, record)
    for job, (ts, record) in all_by_workflow.items():
        status = str(record.get("status", "")).lower()
        grace_minutes = int(CORE_WORKFLOWS[job].get("grace_minutes", 20))
        if status == "started" and (end_dt - ts).total_seconds() > grace_minutes * 60:
            stuck_in_progress += 1

    return {
        "expectedSlots": expected_slots,
        "terminalRuns": terminal_runs,
        "slotAdherencePercent": round(adherence_percent, 2),
        "statusCounts": status_counts,
        "errorCount": len(errors),
        "unrecoveredErrorCount": unrecovered,
        "meanRecoveryMinutes": round(sum(recoveries_minutes) / len(recoveries_minutes), 2)
        if recoveries_minutes
        else 0.0,
        "stuckInProgressCount": stuck_in_progress,
        "byWorkflow": workflow_summaries,
    }


def _paperclip_auth_headers(base_url: str) -> Dict[str, str]:
    key_file = Path.home() / ".openclaw" / "workspace" / "paperclip-claimed-api-key.json"
    token = ""
    if key_file.exists():
        try:
            payload = json.loads(key_file.read_text(encoding="utf-8"))
            token = str(payload.get("token", "")).strip()
        except json.JSONDecodeError:
            token = ""

    is_loopback = base_url.startswith("http://127.0.0.1") or base_url.startswith("http://localhost")
    force_bearer = os.environ.get("PAPERCLIP_USE_BEARER", "0") == "1"
    if force_bearer and token:
        return {"Authorization": f"Bearer {token}"}
    if is_loopback:
        return {"X-Paperclip-Local": "true"}
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {"X-Paperclip-Local": "true"}


def fetch_paperclip_runs(base_url: str, company_id: str) -> List[dict]:
    base = base_url.rstrip("/")
    url = f"{base}/api/companies/{company_id}/heartbeat-runs?limit=1000"
    headers = _paperclip_auth_headers(base_url)
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def usage_number(usage: Optional[Dict[str, Any]], *keys: str) -> float:
    if not usage:
        return 0.0
    for key in keys:
        value = usage.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return 0.0


def summarize_economics(runs: List[dict], start_dt: dt.datetime, end_dt: dt.datetime) -> dict:
    in_window: List[dict] = []
    for run in runs:
        ts = parse_ts(str(run.get("createdAt", "")))
        if ts and start_dt <= ts <= end_dt:
            in_window.append(run)

    total_runs = len(in_window)
    runs_with_usage = 0
    runs_with_cost = 0
    total_input = 0
    total_output = 0
    total_cost = 0.0

    for run in in_window:
        usage = run.get("usageJson")
        usage_record = usage if isinstance(usage, dict) else None
        input_tokens = usage_number(
            usage_record,
            "inputTokens",
            "input_tokens",
            "rawInputTokens",
        )
        output_tokens = usage_number(
            usage_record,
            "outputTokens",
            "output_tokens",
            "rawOutputTokens",
        )
        cost = usage_number(usage_record, "costUsd", "cost_usd", "total_cost_usd")

        if input_tokens > 0 or output_tokens > 0:
            runs_with_usage += 1
        if cost > 0:
            runs_with_cost += 1
        total_input += int(input_tokens)
        total_output += int(output_tokens)
        total_cost += cost

    return {
        "totalRuns": total_runs,
        "runsWithUsage": runs_with_usage,
        "runsWithUsagePercent": round((runs_with_usage / total_runs * 100.0), 2) if total_runs else 0.0,
        "runsWithCost": runs_with_cost,
        "runsWithCostPercent": round((runs_with_cost / total_runs * 100.0), 2) if total_runs else 0.0,
        "totalInputTokens": total_input,
        "totalOutputTokens": total_output,
        "totalCostUsd": round(total_cost, 6),
    }


def run_workflow_health(root: Path, mode: str) -> dict:
    script = root / "tools" / "_workflow_health.py"
    if not script.exists():
        return {"healthy": False, "failures": [{"workflow": "workflow-health", "kind": "missing_script"}]}
    env = os.environ.copy()
    env["WORKSPACE_ROOT"] = str(root)
    try:
        proc = subprocess.run(
            ["python3", str(script), mode],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return {
                "healthy": False,
                "failures": [{"workflow": "workflow-health", "kind": "command_failed", "message": proc.stderr.strip()}],
            }
        payload = json.loads(proc.stdout.strip() or "{}")
        if isinstance(payload, dict):
            return payload
    except (OSError, json.JSONDecodeError):
        pass
    return {"healthy": False, "failures": [{"workflow": "workflow-health", "kind": "invalid_payload"}]}


def render_text(report: dict) -> str:
    lines = [
        "CTO KPI Report (UTC)",
        f"Window: {report['window']['start']} -> {report['window']['end']} ({report['window']['days']} days)",
        "",
        "Reliability:",
        f"- Slot adherence: {report['reliability']['slotAdherencePercent']}%",
        f"- Terminal runs: {report['reliability']['terminalRuns']} / expected slots {report['reliability']['expectedSlots']}",
        f"- Errors: {report['reliability']['errorCount']} (unrecovered: {report['reliability']['unrecoveredErrorCount']})",
        f"- Mean recovery: {report['reliability']['meanRecoveryMinutes']} min",
        f"- Stuck in-progress: {report['reliability']['stuckInProgressCount']}",
        "",
        "Economics:",
        f"- Runs with usage: {report['economics']['runsWithUsagePercent']}% ({report['economics']['runsWithUsage']}/{report['economics']['totalRuns']})",
        f"- Runs with cost: {report['economics']['runsWithCostPercent']}% ({report['economics']['runsWithCost']}/{report['economics']['totalRuns']})",
        f"- Tokens: in {report['economics']['totalInputTokens']} / out {report['economics']['totalOutputTokens']}",
        f"- Cost: ${report['economics']['totalCostUsd']:.6f}",
        "",
        "Workflow Health:",
        f"- Quick healthy: {report['workflowHealth']['quickHealthy']}",
        f"- Full healthy: {report['workflowHealth']['fullHealthy']}",
        f"- Quick failures: {report['workflowHealth']['quickFailureCount']}",
        f"- Full failures: {report['workflowHealth']['fullFailureCount']}",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    try:
        anchor = dt.datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print("invalid --date (expected YYYY-MM-DD)")
        return 1

    root = workspace_root()
    start_dt, end_dt, dates = date_window(anchor, args.days)
    records = read_cron_records(root, dates)
    reliability = summarize_reliability(records, start_dt, end_dt)

    quick = run_workflow_health(root, "audit-quick")
    full = run_workflow_health(root, "audit")

    if args.paperclip_runs_file:
        try:
            run_payload = json.loads(Path(args.paperclip_runs_file).read_text(encoding="utf-8"))
            runs = [item for item in run_payload if isinstance(item, dict)] if isinstance(run_payload, list) else []
        except (OSError, json.JSONDecodeError):
            runs = []
    else:
        runs = fetch_paperclip_runs(args.paperclip_base_url, args.paperclip_company_id)
    economics = summarize_economics(runs, start_dt, end_dt)

    report = {
        "window": {
            "start": start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "days": max(1, int(args.days)),
        },
        "reliability": reliability,
        "economics": economics,
        "workflowHealth": {
            "quickHealthy": bool(quick.get("healthy", False)),
            "fullHealthy": bool(full.get("healthy", False)),
            "quickFailureCount": len(quick.get("failures", []) or []),
            "fullFailureCount": len(full.get("failures", []) or []),
            "quickFailures": quick.get("failures", []) or [],
            "fullFailures": full.get("failures", []) or [],
        },
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        print(render_text(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

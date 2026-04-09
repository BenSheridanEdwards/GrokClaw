#!/usr/bin/env python3
"""Consolidated operator status command for GrokClaw/OpenClaw."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


def workspace_root() -> Path:
    return Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[1]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show consolidated CTO/operator status")
    parser.add_argument("--date", default=dt.datetime.utcnow().strftime("%Y-%m-%d"))
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--offline", action="store_true", help="Skip network health probes")
    return parser.parse_args()


def probe_http(url: str, timeout_seconds: int = 3) -> str:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            if 200 <= int(response.status) < 300:
                return "up"
            return "degraded"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return "down"


def run_kpi_report(root: Path, date: str, days: int) -> Dict[str, Any]:
    script = root / "tools" / "_cto_kpi_report.py"
    if not script.exists():
        return {
            "window": {"start": "", "end": "", "days": max(1, int(days))},
            "reliability": {},
            "economics": {},
            "workflowHealth": {"quickHealthy": False, "fullHealthy": False},
        }
    env = os.environ.copy()
    env["WORKSPACE_ROOT"] = str(root)
    result = subprocess.run(
        ["python3", str(script), "--date", date, "--days", str(max(1, int(days))), "--json"],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {
            "window": {"start": "", "end": "", "days": max(1, int(days))},
            "reliability": {},
            "economics": {},
            "workflowHealth": {"quickHealthy": False, "fullHealthy": False},
            "error": result.stderr.strip() or "kpi_report_failed",
        }
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "window": {"start": "", "end": "", "days": max(1, int(days))},
            "reliability": {},
            "economics": {},
            "workflowHealth": {"quickHealthy": False, "fullHealthy": False},
            "error": "kpi_report_invalid_json",
        }
    return payload if isinstance(payload, dict) else {}


def read_latest_runs(root: Path, limit: int = 8) -> List[Dict[str, Any]]:
    base = root / "data" / "cron-runs"
    entries: List[Dict[str, Any]] = []
    if not base.exists():
        return entries
    for path in sorted(base.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and payload.get("ts"):
                entries.append(payload)
    entries.sort(key=lambda item: str(item.get("ts", "")), reverse=True)
    return entries[:limit]


def render_text(payload: Dict[str, Any]) -> str:
    kpis = payload.get("kpis", {})
    reliability = kpis.get("reliability", {})
    economics = kpis.get("economics", {})
    workflow = kpis.get("workflowHealth", {})
    service_health = payload.get("serviceHealth", {})
    lines = [
        "CTO Status (UTC)",
        f"Gateway: {service_health.get('gateway', 'unknown')}",
        f"Paperclip: {service_health.get('paperclip', 'unknown')}",
        f"Cron slot adherence: {reliability.get('slotAdherencePercent', 'n/a')}%",
        f"Stuck in-progress: {reliability.get('stuckInProgressCount', 'n/a')}",
        f"Workflow quick/full healthy: {workflow.get('quickHealthy', False)} / {workflow.get('fullHealthy', False)}",
        f"Usage coverage: {economics.get('runsWithUsagePercent', 'n/a')}%",
        f"Cost coverage: {economics.get('runsWithCostPercent', 'n/a')}%",
        "",
        "Latest runs:",
    ]
    for item in payload.get("latestRuns", []):
        lines.append(
            f"- {item.get('ts', '')} {item.get('job', '?')} {item.get('status', '?')} "
            f"(runId={item.get('runId', '-')}) {item.get('summary', '')}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = workspace_root()
    kpis = run_kpi_report(root, args.date, args.days)
    if args.offline:
        service_health = {"gateway": "unknown", "paperclip": "unknown"}
    else:
        service_health = {
            "gateway": probe_http("http://127.0.0.1:18800/health"),
            "paperclip": probe_http("http://127.0.0.1:3100/api/health"),
        }

    payload = {
        "generatedAt": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "serviceHealth": service_health,
        "kpis": kpis,
        "latestRuns": read_latest_runs(root),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(render_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

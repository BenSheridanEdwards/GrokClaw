#!/usr/bin/env python3
"""Decide scheduler simplification path from 30-day KPI evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List


def workspace_root() -> Path:
    return Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[1]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scheduler simplification decision gate")
    parser.add_argument("--date", default=dt.datetime.utcnow().strftime("%Y-%m-%d"))
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def run_kpis(root: Path, date: str, days: int) -> Dict[str, Any]:
    script = root / "tools" / "_cto_kpi_report.py"
    if not script.exists():
        return {}
    env = os.environ.copy()
    env["WORKSPACE_ROOT"] = str(root)
    result = subprocess.run(
        ["python3", str(script), "--date", date, "--days", str(max(1, days)), "--json"],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {}
    try:
        payload = json.loads(result.stdout)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def decide(kpis: Dict[str, Any]) -> Dict[str, Any]:
    reliability = kpis.get("reliability", {}) if isinstance(kpis.get("reliability"), dict) else {}
    workflow = kpis.get("workflowHealth", {}) if isinstance(kpis.get("workflowHealth"), dict) else {}

    adherence = float(reliability.get("slotAdherencePercent", 0) or 0)
    stuck = int(reliability.get("stuckInProgressCount", 0) or 0)
    mttr = float(reliability.get("meanRecoveryMinutes", 0) or 0)
    unrecovered = int(reliability.get("unrecoveredErrorCount", 0) or 0)
    full_healthy = bool(workflow.get("fullHealthy", False))

    reasons: List[str] = []
    if adherence < 98.0:
        reasons.append(f"slot adherence below threshold ({adherence:.2f}% < 98.00%)")
    if stuck > 0:
        reasons.append(f"{stuck} stuck in-progress runs observed")
    if unrecovered > 0:
        reasons.append(f"{unrecovered} unrecovered error runs")
    if mttr > 10.0:
        reasons.append(f"mean recovery above threshold ({mttr:.2f}m > 10.00m)")
    if not full_healthy:
        reasons.append("workflow-health full audit not consistently healthy")

    # Readiness score: weighted reliability signal for moving to external queueing.
    readiness_score = 100.0
    readiness_score -= max(0.0, 98.0 - adherence) * 4.0
    readiness_score -= min(20.0, stuck * 5.0)
    readiness_score -= min(20.0, unrecovered * 10.0)
    readiness_score -= min(20.0, max(0.0, mttr - 10.0) * 1.5)
    readiness_score -= 10.0 if not full_healthy else 0.0
    readiness_score = max(0.0, round(readiness_score, 2))

    if reasons:
        decision = "keep_openclaw_cron_consolidate_supervisor"
        rationale = (
            "Keep OpenClaw cron as the core scheduler and reduce operational sprawl first "
            "(watchdog/doctor/health contract consolidation) before introducing a queue migration."
        )
    else:
        decision = "evaluate_external_scheduler_queue"
        rationale = (
            "Reliability metrics are strong enough to evaluate an external scheduler + queue design "
            "without compounding incident risk."
        )

    return {
        "decision": decision,
        "rationale": rationale,
        "reasons": reasons,
        "readinessScore": readiness_score,
        "thresholds": {
            "slotAdherencePercent": ">= 98.00",
            "stuckInProgressCount": "== 0",
            "unrecoveredErrorCount": "== 0",
            "meanRecoveryMinutes": "<= 10.00",
            "workflowHealthFullHealthy": "true",
        },
    }


def render_text(payload: Dict[str, Any]) -> str:
    lines = [
        "Scheduler Simplification Gate",
        f"Decision: {payload['decision']}",
        f"Readiness score: {payload['readinessScore']}",
        f"Rationale: {payload['rationale']}",
    ]
    if payload.get("reasons"):
        lines.append("Blocking factors:")
        for reason in payload["reasons"]:
            lines.append(f"- {reason}")
    else:
        lines.append("Blocking factors: none")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = workspace_root()
    kpis = run_kpis(root, args.date, args.days)
    payload = {
        "window": {
            "date": args.date,
            "days": max(1, int(args.days)),
        },
        "kpis": kpis,
        **decide(kpis),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(render_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple


# NorthStar.md — "How Paperclip Is Used": only core workflows may touch Paperclip.
# Executable check: flag non-core titles only for non-terminal issues (ongoing breach vs closed lifecycle).
TERMINAL_PAPERCLIP_ISSUE_STATUSES = frozenset(
    {"done", "failed", "cancelled", "canceled", "duplicate", "completed"}
)

CORE_WORKFLOWS = {
    "grok-daily-brief": {
        "schedule": {"kind": "daily", "hours": (8,)},
        "grace_minutes": 20,
        "audit_checks": [(("suggestions", "health"), ("Daily system brief:", "Daily system brief (", "Daily Suggestion #", "Daily brief ", "GROKCLAW DAILY BRIEF"))],
    },
"alpha-polymarket": {
        "schedule": {"kind": "hourly", "minute": 0},
        "grace_minutes": 20,
        "research_glob": "data/alpha/research/*.md",
        "agent_report": ("alpha", "alpha-polymarket"),
        # Prefixes must match the hourly Polymarket line in docs/prompts/cron-work-alpha-polymarket.md
        "audit_checks": [
            ("polymarket", ("Alpha session:", "Alpha · Hourly ·", "Alpha (hourly):")),
        ],
    },
}


def utc_now() -> dt.datetime:
    raw = os.environ.get("WORKFLOW_HEALTH_NOW") or os.environ.get("AUDIT_LOG_NOW")
    if raw:
        return dt.datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
    return dt.datetime.utcnow()


def parse_ts(raw: Optional[str]) -> Optional[dt.datetime]:
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def workspace_root() -> Path:
    return Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[1]))


def runtime_cron_path(root: Path) -> Path:
    local = root / ".openclaw" / "cron" / "jobs.json"
    if local.exists():
        return local
    return Path.home() / ".openclaw" / "cron" / "jobs.json"


def add_failure(failures: List[dict], workflow: str, kind: str, message: str) -> None:
    failures.append({"workflow": workflow, "kind": kind, "message": message})


def latest_expected_run(now: dt.datetime, meta: dict) -> dt.datetime:
    schedule = meta["schedule"]
    if schedule["kind"] == "hourly":
        minute = schedule.get("minute", 0)
        candidate = now.replace(minute=minute, second=0, microsecond=0)
        if candidate > now:
            candidate -= dt.timedelta(hours=1)
        return candidate

    hours = sorted(schedule["hours"])
    today_candidates = [now.replace(hour=hour, minute=0, second=0, microsecond=0) for hour in hours]
    past_today = [candidate for candidate in today_candidates if candidate <= now]
    if past_today:
        return past_today[-1]
    yesterday = now - dt.timedelta(days=1)
    return yesterday.replace(hour=hours[-1], minute=0, second=0, microsecond=0)


def previous_expected_run(expected_run: dt.datetime, meta: dict) -> dt.datetime:
    schedule = meta["schedule"]
    if schedule["kind"] == "hourly":
        return expected_run - dt.timedelta(hours=1)

    hours = sorted(schedule["hours"])
    current_hour = expected_run.hour
    for index, hour in enumerate(hours):
        if hour != current_hour:
            continue
        if index > 0:
            return expected_run.replace(hour=hours[index - 1], minute=0, second=0, microsecond=0)
        previous_day = expected_run - dt.timedelta(days=1)
        return previous_day.replace(hour=hours[-1], minute=0, second=0, microsecond=0)
    return expected_run - dt.timedelta(days=1)


def required_run_start(now: dt.datetime, meta: dict) -> dt.datetime:
    expected_run = latest_expected_run(now, meta)
    grace_deadline = expected_run + dt.timedelta(minutes=meta.get("grace_minutes", 0))
    if now < grace_deadline:
        return previous_expected_run(expected_run, meta)
    return expected_run


def format_expected_run(ts: dt.datetime) -> str:
    return ts.strftime("%Y-%m-%d %H:%M UTC")


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_cron_records(root: Path) -> List[dict]:
    records: List[dict] = []
    directory = root / "data" / "cron-runs"
    if not directory.exists():
        return records
    for path in sorted(directory.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def latest_record_for(records: List[dict], job: str) -> Optional[dict]:
    matching = [record for record in records if record.get("job") == job and parse_ts(record.get("ts"))]
    if not matching:
        return None
    return max(matching, key=lambda item: parse_ts(item.get("ts")) or dt.datetime.min)


def has_recent_file(root: Path, pattern: str, earliest: dt.datetime) -> bool:
    for path in root.glob(pattern):
        modified = dt.datetime.utcfromtimestamp(path.stat().st_mtime)
        if modified >= earliest:
            return True
    return False


def _research_dir_from_glob(research_glob: str) -> Path:
    """Directory part of a glob like data/alpha/research/*.md."""
    if "*" in research_glob:
        return Path(research_glob.split("*", 1)[0].rstrip("/"))
    return Path(research_glob).parent


def expected_research_path_for_record(root: Path, job: str, research_glob: str, record_ts: dt.datetime) -> Optional[Path]:
    """Path the workflow prompt names for this job at record_ts (UTC), if known."""
    base = root / _research_dir_from_glob(research_glob)
    if job == "alpha-polymarket":
        return base / f"{record_ts.strftime('%Y-%m-%d-%H')}.md"
    return None


def has_recent_research(
    root: Path,
    job: str,
    research_glob: str,
    earliest: dt.datetime,
    record_ts: Optional[dt.datetime],
) -> bool:
    """True if expected markdown exists for timestamped runs, else fallback to recent-glob check."""
    if record_ts:
        expected = expected_research_path_for_record(root, job, research_glob, record_ts)
        if expected is not None:
            return expected.is_file()
    return has_recent_file(root, research_glob, earliest)


def load_agent_reports(root: Path) -> List[dict]:
    reports: List[dict] = []
    directory = root / "data" / "agent-reports"
    if not directory.exists():
        return reports
    for path in sorted(directory.glob("*.json")):
        try:
            payload = load_json(path)
        except json.JSONDecodeError:
            continue
        for entry in payload.get("reports", []):
            reports.append(entry)
    return reports


def has_recent_agent_report(root: Path, agent: str, job: str, earliest: dt.datetime) -> bool:
    for report in load_agent_reports(root):
        if report.get("agent") != agent or report.get("job") != job:
            continue
        timestamp = parse_ts(report.get("timestamp"))
        if timestamp and timestamp >= earliest:
            return True
    return False


def load_audit_logs(root: Path) -> List[dict]:
    events: List[dict] = []
    directory = root / "data" / "audit-log"
    if not directory.exists():
        return events
    for path in sorted(directory.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def has_recent_audit_event(root: Path, topic_names, prefixes: tuple[str, ...], earliest: dt.datetime) -> bool:
    if isinstance(topic_names, str):
        allowed_topics = {topic_names}
    else:
        allowed_topics = set(topic_names)
    for event in load_audit_logs(root):
        if event.get("topic") not in allowed_topics:
            continue
        timestamp = parse_ts(event.get("ts"))
        if not timestamp or timestamp < earliest:
            continue
        message = (event.get("message") or "").strip()
        if any(message.startswith(prefix) for prefix in prefixes):
            return True
    return False


def fetch_paperclip_issues() -> List[dict]:
    override = os.environ.get("WORKFLOW_HEALTH_PAPERCLIP_ISSUES_FILE")
    if override:
        payload = load_json(Path(override))
        return payload if isinstance(payload, list) else payload.get("items", [])

    key_file = Path.home() / ".openclaw" / "workspace" / "paperclip-claimed-api-key.json"
    token = ""
    if key_file.exists():
        try:
            token = load_json(key_file).get("token", "")
        except Exception:
            token = ""

    headers: dict = {"Content-Type": "application/json"}
    # Match tools/paperclip-api.sh: loopback trusts X-Paperclip-Local; Bearer breaks some routes.
    use_bearer = (os.environ.get("PAPERCLIP_USE_BEARER") or "").strip().lower() in ("1", "true", "yes")
    if use_bearer and token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Paperclip-Local"] = "true"

    request = urllib.request.Request(
        f"http://127.0.0.1:3100/api/companies/{os.environ['PAPERCLIP_COMPANY_ID']}/issues",
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        payload = json.load(response)
    return payload if isinstance(payload, list) else payload.get("items", [])


def issue_timestamp(issue: dict) -> Optional[dt.datetime]:
    for key in ("updatedAt", "createdAt", "lastActivityAt"):
        parsed = parse_ts(issue.get(key))
        if parsed:
            return parsed
    return None


def find_recent_issue(issues: List[dict], job: str, earliest: dt.datetime) -> Optional[dict]:
    matches = []
    for issue in issues:
        title = issue.get("title", "")
        if not title.startswith(f"[{job}]"):
            continue
        timestamp = issue_timestamp(issue)
        if timestamp and timestamp >= earliest:
            matches.append((timestamp, issue))
    if not matches:
        return None
    return max(matches, key=lambda item: item[0])[1]


def runtime_cron_matches(root: Path) -> Tuple[bool, str]:
    repo_path = root / "cron" / "jobs.json"
    rt_path = runtime_cron_path(root)
    if not repo_path.exists():
        return False, "repo cron/jobs.json missing"
    if not rt_path.exists():
        return False, f"runtime cron missing at {rt_path}"
    repo_names = [job.get("name") for job in load_json(repo_path).get("jobs", [])]
    runtime_names = [job.get("name") for job in load_json(rt_path).get("jobs", [])]
    expected = set(CORE_WORKFLOWS.keys())
    repo_set = set(repo_names)
    runtime_set = set(runtime_names)
    if not expected.issubset(repo_set):
        missing = ", ".join(sorted(expected - repo_set))
        return False, f"repo cron/jobs.json is missing core workflows: {missing}"
    if not expected.issubset(runtime_set):
        missing = ", ".join(sorted(expected - runtime_set))
        return False, f"runtime cron is missing core workflows: {missing}"
    return True, ""


HUMAN_LABELS = {
    "missing_run": "did not run",
    "stale_run": "last run is stale",
    "in_progress_run": "still in progress",
    "error_run": "last run errored",
    "missing_research": "no research file written",
    "missing_agent_report": "no agent report written",
    "missing_audit": "no Telegram post found",
    "missing_paperclip": "no Paperclip issue created",
    "open_paperclip": "Paperclip issue left open",
    "cron_drift": "cron config out of sync",
    "non_core_paperclip": "non-core job touched Paperclip",
    "paperclip_unavailable": "Paperclip is unreachable",
}

REMEDIATION_HINTS = {
    "missing_run": "tap Rerun below or: OPENCLAW_AGENT_ID={agent} ./tools/run-openclaw-agent.sh",
    "stale_run": "tap Rerun below or: OPENCLAW_AGENT_ID={agent} ./tools/run-openclaw-agent.sh",
    "in_progress_run": "check the active run, then re-run if it is stuck",
    "error_run": "check gateway logs for the root cause, then re-run",
    "missing_research": "the agent ran but didn't write output — check the prompt",
    "missing_agent_report": "the agent didn't report — check the cron prompt",
    "missing_audit": "the agent didn't post to Telegram — check the cron prompt",
    "missing_paperclip": "Paperclip lifecycle didn't start — check cron-paperclip-lifecycle.sh",
    "open_paperclip": "Paperclip issue wasn't closed — the agent likely crashed mid-run",
    "cron_drift": "sync cron: ./tools/sync-cron-jobs.sh --restart",
    "non_core_paperclip": "a non-core job touched Paperclip — policy violation",
    "paperclip_unavailable": "Paperclip is down — restart it",
}

WORKFLOW_AGENTS = {
    "grok-daily-brief": "grok",
    "alpha-polymarket": "alpha",
}


def _remediation(failure: dict) -> str:
    kind = failure.get("kind", "")
    hint = REMEDIATION_HINTS.get(kind, "investigate in gateway logs")
    agent = WORKFLOW_AGENTS.get(failure.get("workflow", ""), "grok")
    return hint.format(agent=agent)


def _human_label(kind: str) -> str:
    return HUMAN_LABELS.get(kind, kind.replace("_", " "))


def build_alert_message(failures: List[dict]) -> str:
    if not failures:
        return "Workflow health: all clear"

    by_workflow: dict[str, List[dict]] = {}
    for f in failures:
        by_workflow.setdefault(f["workflow"], []).append(f)

    lines = []
    for wf, wf_failures in by_workflow.items():
        labels = ", ".join(_human_label(f["kind"]) for f in wf_failures)
        lines.append(f"{wf}: {labels}")

    first = failures[0]
    lines.append("")
    lines.append(_remediation(first))

    return "\n".join(lines)


def build_draft(failures: List[dict], failure_hash: str) -> dict:
    evidence_lines = "\n".join(
        f"- {f['workflow']}: {_human_label(f['kind'])}" for f in failures[:8]
    )
    remediation_lines = "\n".join(
        f"- {f['workflow']}: {_remediation(f)}" for f in failures[:8]
    )
    return {
        "id": f"workflow-health-{failure_hash[:12]}",
        "title": "Fix workflow health failure in core cron workflows",
        "description": (
            "Problem:\n"
            "One or more core workflows didn't complete.\n\n"
            "Evidence:\n"
            f"{evidence_lines}\n\n"
            "Suggested fixes:\n"
            f"{remediation_lines}\n\n"
            "Or run: ./tools/grokclaw-doctor.sh --heal"
        ),
    }


def build_result(failures: List[dict]) -> dict:
    healthy = not failures
    failure_blob = json.dumps(sorted(failures, key=lambda item: (item["workflow"], item["kind"], item["message"])), sort_keys=True)
    failure_hash = hashlib.sha256(failure_blob.encode("utf-8")).hexdigest()[:12]
    return {
        "healthy": healthy,
        "failureHash": failure_hash,
        "failures": failures,
        "alertMessage": build_alert_message(failures),
        "draft": build_draft(failures, failure_hash) if failures else None,
    }


def audit_job(
    root: Path,
    now: dt.datetime,
    job: str,
    meta: dict,
    records: List[dict],
    failures: List[dict],
    *,
    issues: Optional[List[dict]] = None,
) -> None:
    earliest = required_run_start(now, meta)
    record = latest_record_for(records, job)
    if not record:
        add_failure(failures, job, "missing_run", f"{job} has no cron-run evidence for expected run at {format_expected_run(earliest)}")
        return
    record_ts = parse_ts(record.get("ts"))
    if not record_ts or record_ts < earliest:
        add_failure(failures, job, "stale_run", f"{job} has not completed its expected run at {format_expected_run(earliest)}")
        return
    if record.get("status") == "started":
        add_failure(failures, job, "in_progress_run", f"{job} started at {record.get('ts', 'unknown time')} and is still in progress after the grace window")
        return
    if record.get("status") == "error":
        add_failure(failures, job, "error_run", f"{job} last run recorded error: {record.get('summary', '')}".strip())

    research_glob = meta.get("research_glob")
    if research_glob and not has_recent_research(root, job, research_glob, earliest, record_ts):
        add_failure(failures, job, "missing_research", f"{job} is missing research markdown in {research_glob.rsplit('/', 1)[0]}")

    agent_report = meta.get("agent_report")
    if agent_report and not has_recent_agent_report(root, agent_report[0], agent_report[1], earliest):
        add_failure(failures, job, "missing_agent_report", f"{job} is missing a recent agent report")

    audit_checks = meta.get("audit_checks", [])
    for topic, prefixes in audit_checks:
        if not has_recent_audit_event(root, topic, prefixes, earliest):
            add_failure(failures, job, "missing_audit", f"{job} is missing recent audit-log evidence for topic {topic}")

    if issues is None:
        return

    issue = find_recent_issue(issues, job, earliest)
    if not issue:
        add_failure(failures, job, "missing_paperclip", f"{job} is missing a recent Paperclip issue")
    elif issue.get("status") not in {"done", "failed", "cancelled"}:
        add_failure(failures, job, "open_paperclip", f"{job} Paperclip issue is not closed (status={issue.get('status')})")


def audit() -> dict:
    root = workspace_root()
    now = utc_now()
    failures: List[dict] = []

    cron_ok, cron_message = runtime_cron_matches(root)
    if not cron_ok:
        add_failure(failures, "scheduler", "cron_drift", cron_message)

    try:
        issues = fetch_paperclip_issues()
    except Exception as exc:  # pragma: no cover - exercised in integration, not unit test
        issues = []
        add_failure(failures, "paperclip", "paperclip_unavailable", f"Paperclip issues unavailable: {exc}")

    non_core_seen = set()
    for issue in issues:
        title = issue.get("title", "")
        match = re.match(r"^\[([^\]]+)\]", title)
        if not match:
            continue
        job = match.group(1)
        timestamp = issue_timestamp(issue)
        status = (issue.get("status") or "").strip().lower()
        if status in TERMINAL_PAPERCLIP_ISSUE_STATUSES:
            continue
        if job not in CORE_WORKFLOWS and timestamp and timestamp >= now - dt.timedelta(hours=48):
            non_core_seen.add(job)
    for job in sorted(non_core_seen):
        add_failure(failures, "paperclip", "non_core_paperclip", f"non-core workflow touched Paperclip: {job}")

    records = load_cron_records(root)
    for job, meta in CORE_WORKFLOWS.items():
        audit_job(root, now, job, meta, records, failures, issues=issues)

    return build_result(failures)


def audit_one(job: str, *, include_paperclip: bool = False) -> dict:
    root = workspace_root()
    now = utc_now()
    failures: List[dict] = []
    meta = CORE_WORKFLOWS[job]
    records = load_cron_records(root)
    issues = fetch_paperclip_issues() if include_paperclip else None
    audit_job(root, now, job, meta, records, failures, issues=issues)
    return build_result(failures)


def audit_quick() -> dict:
    root = workspace_root()
    now = utc_now()
    failures: List[dict] = []

    cron_ok, cron_message = runtime_cron_matches(root)
    if not cron_ok:
        add_failure(failures, "scheduler", "cron_drift", cron_message)

    records = load_cron_records(root)
    for job, meta in CORE_WORKFLOWS.items():
        earliest = required_run_start(now, meta)
        record = latest_record_for(records, job)
        if not record:
            add_failure(failures, job, "missing_run", f"{job} has no cron-run evidence for expected run at {format_expected_run(earliest)}")
            continue
        record_ts = parse_ts(record.get("ts"))
        if not record_ts or record_ts < earliest:
            add_failure(failures, job, "stale_run", f"{job} has not completed its expected run at {format_expected_run(earliest)}")
            continue
        if record.get("status") == "started":
            add_failure(failures, job, "in_progress_run", f"{job} started at {record.get('ts', 'unknown time')} and is still in progress after the grace window")
            continue
        if record.get("status") == "error":
            add_failure(failures, job, "error_run", f"{job} last run recorded error: {record.get('summary', '')}".strip())

    return build_result(failures)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: _workflow_health.py <audit|audit-one|audit-quick|paperclip-allowed> [...]", file=sys.stderr)
        return 1

    command = argv[1]
    if command == "paperclip-allowed":
        if len(argv) != 3:
            print("usage: _workflow_health.py paperclip-allowed <job>", file=sys.stderr)
            return 1
        if argv[2] in CORE_WORKFLOWS:
            return 0
        print("only core workflows may touch Paperclip", file=sys.stderr)
        return 1

    if command == "audit":
        print(json.dumps(audit(), ensure_ascii=False))
        return 0

    if command == "audit-one":
        if len(argv) not in {3, 4}:
            print("usage: _workflow_health.py audit-one <job> [--include-paperclip]", file=sys.stderr)
            return 1
        job = argv[2]
        if job not in CORE_WORKFLOWS:
            print(f"unknown core workflow: {job}", file=sys.stderr)
            return 1
        include_paperclip = len(argv) == 4 and argv[3] == "--include-paperclip"
        if len(argv) == 4 and not include_paperclip:
            print("usage: _workflow_health.py audit-one <job> [--include-paperclip]", file=sys.stderr)
            return 1
        print(json.dumps(audit_one(job, include_paperclip=include_paperclip), ensure_ascii=False))
        return 0

    if command == "audit-quick":
        print(json.dumps(audit_quick(), ensure_ascii=False))
        return 0

    print(f"unknown command: {command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

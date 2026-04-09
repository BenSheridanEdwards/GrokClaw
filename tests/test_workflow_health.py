import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


class WorkflowHealthTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "_workflow_health.py"

    def _run_audit(self, workspace: Path, now: str, paperclip_payload: object) -> dict:
        paperclip_file = workspace / "paperclip-issues.json"
        paperclip_file.write_text(json.dumps(paperclip_payload), encoding="utf-8")
        env = os.environ.copy()
        env["WORKSPACE_ROOT"] = str(workspace)
        env["WORKFLOW_HEALTH_NOW"] = now
        env["WORKFLOW_HEALTH_PAPERCLIP_ISSUES_FILE"] = str(paperclip_file)
        result = subprocess.run(
            ["python3", str(self.script), "audit"],
            cwd=str(self.workspace),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def _run_json_command(self, workspace: Path, now: str, command: str, *args: str) -> dict:
        env = os.environ.copy()
        env["WORKSPACE_ROOT"] = str(workspace)
        env["WORKFLOW_HEALTH_NOW"] = now
        result = subprocess.run(
            ["python3", str(self.script), command, *args],
            cwd=str(self.workspace),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def _seed_core_jobs(self, workspace: Path) -> None:
        (workspace / "cron").mkdir(parents=True, exist_ok=True)
        (workspace / ".openclaw" / "cron").mkdir(parents=True, exist_ok=True)
        jobs = {
            "jobs": [
                {"id": "1", "name": "grok-daily-brief", "schedule": {"kind": "cron", "expr": "0 8 * * *"}, "payload": {}, "delivery": {}},
                {"id": "2", "name": "grok-openclaw-research", "schedule": {"kind": "cron", "expr": "0 7,13,19 * * *"}, "payload": {}, "delivery": {}},
                {"id": "3", "name": "alpha-polymarket", "schedule": {"kind": "cron", "expr": "0 * * * *"}, "payload": {}, "delivery": {}, "agentId": "alpha"},
            ]
        }
        for path in [workspace / "cron" / "jobs.json", workspace / ".openclaw" / "cron" / "jobs.json"]:
            path.write_text(json.dumps(jobs), encoding="utf-8")

    def _seed_full_evidence(self, workspace: Path, alpha_ts: str, research_ts: str, brief_ts: str) -> list[dict]:
        (workspace / "data" / "cron-runs").mkdir(parents=True, exist_ok=True)
        (workspace / "data" / "alpha" / "research").mkdir(parents=True, exist_ok=True)
        (workspace / "data" / "research" / "openclaw").mkdir(parents=True, exist_ok=True)
        (workspace / "data" / "agent-reports").mkdir(parents=True, exist_ok=True)
        (workspace / "data" / "audit-log").mkdir(parents=True, exist_ok=True)

        (workspace / "data" / "cron-runs" / "2026-04-01.jsonl").write_text(
            "\n".join(
                [
                    json.dumps({"job": "grok-daily-brief", "agent": "grok", "ts": brief_ts, "status": "ok", "summary": "posted brief"}),
                    json.dumps({"job": "grok-openclaw-research", "agent": "grok", "ts": research_ts, "status": "ok", "summary": "saved research"}),
                    json.dumps({"job": "alpha-polymarket", "agent": "alpha", "ts": alpha_ts, "status": "ok", "summary": "alpha summary"}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        research_dt = datetime.strptime(research_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        alpha_dt = datetime.strptime(alpha_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        research_slot = {7: "morning", 13: "afternoon", 19: "evening"}.get(research_dt.hour)
        research_name = (
            f"{research_dt.strftime('%Y-%m-%d')}-{research_slot}.md"
            if research_slot
            else f"{research_dt.strftime('%Y-%m-%d')}.md"
        )
        alpha_name = f"{alpha_dt.strftime('%Y-%m-%d-%H')}.md"
        research_path = workspace / "data" / "research" / "openclaw" / research_name
        alpha_path = workspace / "data" / "alpha" / "research" / alpha_name
        research_path.write_text("# research\n", encoding="utf-8")
        alpha_path.write_text("# alpha\n", encoding="utf-8")
        os.utime(research_path, (research_dt.timestamp(), research_dt.timestamp()))
        os.utime(alpha_path, (alpha_dt.timestamp(), alpha_dt.timestamp()))

        (workspace / "data" / "agent-reports" / "2026-04-01.json").write_text(
            json.dumps(
                {
                    "reports": [
                        {"agent": "alpha", "job": "alpha-polymarket", "timestamp": alpha_ts, "summary": "alpha summary"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        (workspace / "data" / "audit-log" / "2026-04-01.jsonl").write_text(
            "\n".join(
                [
                    json.dumps({"ts": "2026-04-01T08:06:00Z", "kind": "telegram_post", "topic": "suggestions", "message": "Daily system brief: all core workflows healthy."}),
                    json.dumps({"ts": research_ts, "kind": "telegram_post", "topic": "health", "message": "OpenClaw research (morning): all good"}),
                    json.dumps({"ts": alpha_ts, "kind": "telegram_post", "topic": "polymarket", "message": "Alpha session: trade. Why: edge found."}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return [
            {"id": "issue-daily", "title": "[grok-daily-brief] 2026-04-01 08:00 UTC", "status": "done", "updatedAt": "2026-04-01T08:06:00Z"},
            {"id": "issue-research", "title": "[grok-openclaw-research] 2026-04-01 07:00 UTC", "status": "done", "updatedAt": research_ts},
            {"id": "issue-alpha", "title": "[alpha-polymarket] 2026-04-01 09:00 UTC", "status": "done", "updatedAt": alpha_ts},
        ]

    def _read_audit_events(self, workspace: Path) -> list[dict]:
        return [
            json.loads(line)
            for line in (workspace / "data" / "audit-log" / "2026-04-01.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _write_audit_events(self, workspace: Path, events: list[dict]) -> None:
        (workspace / "data" / "audit-log" / "2026-04-01.jsonl").write_text(
            "\n".join(json.dumps(event) for event in events) + "\n",
            encoding="utf-8",
        )

    def _read_agent_reports(self, workspace: Path) -> dict:
        return json.loads((workspace / "data" / "agent-reports" / "2026-04-01.json").read_text(encoding="utf-8"))

    def _write_agent_reports(self, workspace: Path, payload: dict) -> None:
        (workspace / "data" / "agent-reports" / "2026-04-01.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def test_reports_healthy_when_core_workflow_leaves_full_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "data" / "cron-runs").mkdir(parents=True)
            (workspace / "data" / "alpha" / "research").mkdir(parents=True)
            (workspace / "data" / "agent-reports").mkdir(parents=True)
            (workspace / "data" / "audit-log").mkdir(parents=True)
            (workspace / "cron").mkdir(parents=True)
            (workspace / ".openclaw" / "cron").mkdir(parents=True)

            jobs = {
                "jobs": [
                    {"id": "1", "name": "grok-daily-brief", "schedule": {"kind": "cron", "expr": "0 8 * * *"}, "payload": {}, "delivery": {}},
                    {"id": "2", "name": "grok-openclaw-research", "schedule": {"kind": "cron", "expr": "0 7,13,19 * * *"}, "payload": {}, "delivery": {}},
                    {"id": "3", "name": "alpha-polymarket", "schedule": {"kind": "cron", "expr": "0 * * * *"}, "payload": {}, "delivery": {}, "agentId": "alpha"},
                ]
            }
            for path in [workspace / "cron" / "jobs.json", workspace / ".openclaw" / "cron" / "jobs.json"]:
                path.write_text(json.dumps(jobs), encoding="utf-8")

            (workspace / "data" / "cron-runs" / "2026-04-01.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "job": "grok-daily-brief",
                                "agent": "grok",
                                "ts": "2026-04-01T08:05:00Z",
                                "status": "ok",
                                "summary": "posted brief",
                            }
                        ),
                        json.dumps(
                            {
                                "job": "grok-openclaw-research",
                                "agent": "grok",
                                "ts": "2026-04-01T07:05:00Z",
                                "status": "ok",
                                "summary": "saved morning research",
                            }
                        ),
                        json.dumps(
                            {
                                "job": "alpha-polymarket",
                                "agent": "alpha",
                                "ts": "2026-04-01T10:10:00Z",
                                "status": "ok",
                                "summary": "placed one trade",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (workspace / "data" / "research" / "openclaw").mkdir(parents=True)
            (workspace / "data" / "research" / "openclaw" / "2026-04-01-morning.md").write_text("# research\n", encoding="utf-8")
            (workspace / "data" / "alpha" / "research" / "2026-04-01-10.md").write_text("# alpha run\n", encoding="utf-8")
            openclaw_epoch = datetime.strptime("2026-04-01T07:06:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
            alpha_epoch = datetime.strptime("2026-04-01T10:12:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
            os.utime(workspace / "data" / "research" / "openclaw" / "2026-04-01-morning.md", (openclaw_epoch, openclaw_epoch))
            os.utime(workspace / "data" / "alpha" / "research" / "2026-04-01-10.md", (alpha_epoch, alpha_epoch))
            (workspace / "data" / "agent-reports" / "2026-04-01.json").write_text(
                json.dumps(
                    {
                        "reports": [
                            {
                                "agent": "alpha",
                                "job": "alpha-polymarket",
                                "timestamp": "2026-04-01T10:11:00Z",
                                "summary": "placed one trade",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (workspace / "data" / "audit-log" / "2026-04-01.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "ts": "2026-04-01T08:06:00Z",
                                "kind": "telegram_post",
                                "topic": "suggestions",
                                "message": "Daily system brief: all core workflows healthy.",
                            }
                        ),
                        json.dumps(
                            {
                                "ts": "2026-04-01T07:06:00Z",
                                "kind": "telegram_post",
                                "topic": "health",
                                "message": "OpenClaw research (morning): all good",
                            }
                        ),
                        json.dumps(
                            {
                                "ts": "2026-04-01T10:12:00Z",
                                "kind": "telegram_post",
                                "topic": "polymarket",
                                "message": "Alpha session: trade. Why: edge found.",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            payload = [
                {
                    "id": "issue-daily",
                    "title": "[grok-daily-brief] 2026-04-01 08:00 UTC",
                    "status": "done",
                    "updatedAt": "2026-04-01T08:06:00Z",
                },
                {
                    "id": "issue-research",
                    "title": "[grok-openclaw-research] 2026-04-01 07:00 UTC",
                    "status": "done",
                    "updatedAt": "2026-04-01T07:06:00Z",
                },
                {
                    "id": "issue-1",
                    "title": "[alpha-polymarket] 2026-04-01 10:00 UTC",
                    "status": "done",
                    "updatedAt": "2026-04-01T10:12:00Z",
                },
            ]

            report = self._run_audit(workspace, "2026-04-01T10:30:00Z", payload)
            self.assertTrue(report["healthy"])
            self.assertEqual(report["failures"], [])

    def test_accepts_extra_non_core_cron_jobs_when_core_workflows_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            repo_jobs = json.loads((workspace / "cron" / "jobs.json").read_text(encoding="utf-8"))
            runtime_jobs = json.loads((workspace / ".openclaw" / "cron" / "jobs.json").read_text(encoding="utf-8"))
            extra_job = {"id": "5", "name": "doctor-backfill", "schedule": {"kind": "cron", "expr": "15 * * * *"}, "payload": {}, "delivery": {}}
            repo_jobs["jobs"].append(extra_job)
            runtime_jobs["jobs"].append(extra_job)
            (workspace / "cron" / "jobs.json").write_text(json.dumps(repo_jobs), encoding="utf-8")
            (workspace / ".openclaw" / "cron" / "jobs.json").write_text(json.dumps(runtime_jobs), encoding="utf-8")
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T10:10:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )

            report = self._run_audit(workspace, "2026-04-01T10:30:00Z", payload)
            self.assertTrue(report["healthy"], msg=report)

    def test_accepts_paperclip_issue_timestamps_with_milliseconds(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T10:10:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )
            payload_ms = []
            for issue in payload:
                updated = issue["updatedAt"].replace("Z", ".123Z")
                payload_ms.append({**issue, "updatedAt": updated})

            report = self._run_audit(workspace, "2026-04-01T10:30:00Z", payload_ms)
            self.assertTrue(report["healthy"], msg=report)

    def test_reports_missing_evidence_and_non_core_paperclip_activity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "data" / "cron-runs").mkdir(parents=True)
            (workspace / "data" / "audit-log").mkdir(parents=True)
            (workspace / "cron").mkdir(parents=True)
            (workspace / ".openclaw" / "cron").mkdir(parents=True)

            jobs = {
                "jobs": [
                    {"id": "1", "name": "grok-daily-brief", "schedule": {"kind": "cron", "expr": "0 8 * * *"}, "payload": {}, "delivery": {}},
                    {"id": "2", "name": "grok-openclaw-research", "schedule": {"kind": "cron", "expr": "0 7,13,19 * * *"}, "payload": {}, "delivery": {}},
                    {"id": "3", "name": "alpha-polymarket", "schedule": {"kind": "cron", "expr": "0 * * * *"}, "payload": {}, "delivery": {}, "agentId": "alpha"},
                ]
            }
            for path in [workspace / "cron" / "jobs.json", workspace / ".openclaw" / "cron" / "jobs.json"]:
                path.write_text(json.dumps(jobs), encoding="utf-8")

            (workspace / "data" / "cron-runs" / "2026-04-01.jsonl").write_text(
                json.dumps(
                    {
                        "job": "grok-openclaw-research",
                        "agent": "grok",
                        "ts": "2026-04-01T07:05:00Z",
                        "status": "ok",
                        "summary": "reported research",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            payload = [
                {
                    "id": "issue-1",
                    "title": "[pr-watch] 2026-04-01 07:00 UTC",
                    "status": "todo",
                    "updatedAt": "2026-04-01T07:10:00Z",
                }
            ]

            report = self._run_audit(workspace, "2026-04-01T13:30:00Z", payload)
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("grok-openclaw-research has not completed its expected run", messages)
            self.assertIn("non-core workflow touched Paperclip", messages)
            self.assertTrue(report["draft"]["title"])
            self.assertIn("workflow health", report["draft"]["title"].lower())

    def test_daily_brief_requires_the_latest_expected_run_after_grace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T09:10:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-03-31T08:05:00Z",
            )

            report = self._run_audit(workspace, "2026-04-01T08:30:00Z", payload)
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("grok-daily-brief", messages)

    def test_openclaw_research_requires_the_latest_expected_run_after_grace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T12:10:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )

            report = self._run_audit(workspace, "2026-04-01T13:30:00Z", payload)
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("grok-openclaw-research", messages)

    def test_alpha_requires_the_latest_expected_run_after_grace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T09:10:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )

            report = self._run_audit(workspace, "2026-04-01T10:30:00Z", payload)
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("alpha-polymarket", messages)

    def test_daily_brief_happy_path_satisfies_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T08:10:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )

            report = self._run_audit(workspace, "2026-04-01T08:30:00Z", payload)
            self.assertTrue(report["healthy"])

    def test_daily_brief_accepts_health_topic_fallback_prefix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T08:10:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )
            events = self._read_audit_events(workspace)
            events = [event for event in events if event["topic"] != "suggestions"]
            events.append(
                {
                    "ts": "2026-04-01T08:06:30Z",
                    "kind": "telegram_post",
                    "topic": "health",
                    "message": "Daily brief 2026-04-01: core workflows healthy.",
                }
            )
            self._write_audit_events(workspace, events)

            report = self._run_audit(workspace, "2026-04-01T08:30:00Z", payload)
            self.assertTrue(report["healthy"], msg=report)

    def test_daily_brief_sad_path_flags_missing_audit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T08:10:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )
            events = [event for event in self._read_audit_events(workspace) if event["topic"] != "suggestions"]
            self._write_audit_events(workspace, events)

            report = self._run_audit(workspace, "2026-04-01T08:30:00Z", payload)
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("grok-daily-brief is missing recent audit-log evidence", messages)

    def test_openclaw_research_happy_path_satisfies_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T13:10:00Z",
                research_ts="2026-04-01T13:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )

            report = self._run_audit(workspace, "2026-04-01T13:30:00Z", payload)
            self.assertTrue(report["healthy"])

    def test_openclaw_research_sad_path_flags_missing_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T13:10:00Z",
                research_ts="2026-04-01T13:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )
            (workspace / "data" / "research" / "openclaw" / "2026-04-01-afternoon.md").unlink()

            report = self._run_audit(workspace, "2026-04-01T13:30:00Z", payload)
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("grok-openclaw-research is missing research markdown", messages)

    def test_research_passes_when_expected_file_exists_despite_stale_mtime(self):
        """Git checkout preserves old mtimes; audit keys off cron record + prompt filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T13:10:00Z",
                research_ts="2026-04-01T13:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )
            openclaw_dir = workspace / "data" / "research" / "openclaw"
            (openclaw_dir / "2026-04-01.md").unlink(missing_ok=True)
            afternoon = openclaw_dir / "2026-04-01-afternoon.md"
            afternoon.write_text("# afternoon brief\n", encoding="utf-8")
            os.utime(afternoon, (1, 1))

            events = self._read_audit_events(workspace)
            for event in events:
                if event.get("topic") == "health" and "OpenClaw research" in event.get("message", ""):
                    event["ts"] = "2026-04-01T13:06:00Z"
                    event["message"] = "OpenClaw research (afternoon): headline"
            self._write_audit_events(workspace, events)

            payload = [issue for issue in payload if "grok-openclaw-research" not in issue.get("title", "")]
            payload.append(
                {
                    "id": "issue-research-afternoon",
                    "title": "[grok-openclaw-research] 2026-04-01 13:00 UTC",
                    "status": "done",
                    "updatedAt": "2026-04-01T13:06:00Z",
                }
            )

            cron_path = workspace / "data" / "cron-runs" / "2026-04-01.jsonl"
            lines = [json.loads(line) for line in cron_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            lines = [rec for rec in lines if rec.get("job") != "grok-openclaw-research"]
            lines.append(
                {
                    "job": "grok-openclaw-research",
                    "agent": "grok",
                    "ts": "2026-04-01T13:06:00Z",
                    "status": "ok",
                    "summary": "saved afternoon research",
                }
            )
            cron_path.write_text("\n".join(json.dumps(rec) for rec in lines) + "\n", encoding="utf-8")

            report = self._run_audit(workspace, "2026-04-01T13:30:00Z", payload)
            self.assertTrue(report["healthy"], msg=report.get("failures"))

    def test_alpha_happy_path_satisfies_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T10:10:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )

            report = self._run_audit(workspace, "2026-04-01T10:30:00Z", payload)
            self.assertTrue(report["healthy"])

    def test_alpha_sad_path_flags_missing_agent_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T10:10:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )
            reports = self._read_agent_reports(workspace)
            reports["reports"] = [entry for entry in reports["reports"] if entry["agent"] != "alpha"]
            self._write_agent_reports(workspace, reports)

            report = self._run_audit(workspace, "2026-04-01T10:30:00Z", payload)
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("alpha-polymarket is missing a recent agent report", messages)

    def test_audit_one_uses_local_evidence_for_single_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T10:10:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )

            report = self._run_json_command(
                workspace,
                "2026-04-01T10:30:00Z",
                "audit-one",
                "alpha-polymarket",
            )
            self.assertTrue(report["healthy"])
            self.assertEqual(report["failures"], [])

    def test_audit_one_can_include_paperclip_checks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T10:10:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )
            payload = [issue for issue in payload if "alpha-polymarket" not in issue.get("title", "")]
            paperclip_file = workspace / "paperclip-issues.json"
            paperclip_file.write_text(json.dumps(payload), encoding="utf-8")

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["WORKFLOW_HEALTH_NOW"] = "2026-04-01T10:30:00Z"
            env["WORKFLOW_HEALTH_PAPERCLIP_ISSUES_FILE"] = str(paperclip_file)
            result = subprocess.run(
                ["python3", str(self.script), "audit-one", "alpha-polymarket", "--include-paperclip"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            report = json.loads(result.stdout)
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("alpha-polymarket is missing a recent Paperclip issue", messages)

    def test_audit_quick_flags_missing_hourly_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            (workspace / "data" / "cron-runs").mkdir(parents=True, exist_ok=True)
            (workspace / "data" / "cron-runs" / "2026-04-01.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"job": "grok-daily-brief", "agent": "grok", "ts": "2026-04-01T08:05:00Z", "status": "ok", "summary": "posted brief"}),
                        json.dumps({"job": "grok-openclaw-research", "agent": "grok", "ts": "2026-04-01T13:02:00Z", "status": "ok", "summary": "research saved"}),
                        json.dumps({"job": "alpha-polymarket", "agent": "alpha", "ts": "2026-04-01T13:05:00Z", "status": "ok", "summary": "alpha ok"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = self._run_json_command(
                workspace,
                "2026-04-01T14:30:00Z",
                "audit-quick",
            )
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("alpha-polymarket", messages)

    def test_started_run_after_grace_is_reported_as_stuck(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            (workspace / "data" / "cron-runs").mkdir(parents=True, exist_ok=True)
            (workspace / "data" / "cron-runs" / "2026-04-01.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"job": "grok-daily-brief", "agent": "grok", "ts": "2026-04-01T08:05:00Z", "status": "ok", "summary": "posted brief"}),
                        json.dumps({"job": "grok-openclaw-research", "agent": "grok", "ts": "2026-04-01T13:02:00Z", "status": "ok", "summary": "research saved"}),
                        json.dumps({"job": "alpha-polymarket", "agent": "alpha", "ts": "2026-04-01T14:01:00Z", "status": "started", "summary": "run started"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = self._run_json_command(
                workspace,
                "2026-04-01T14:30:00Z",
                "audit-quick",
            )
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("alpha-polymarket", messages)
            self.assertIn("still in progress", messages)

    def test_audit_one_alpha_polymarket_accepts_new_telegram_prefix_and_trim(self):
        """Hourly line may use Alpha · Hourly · / Alpha (hourly): and leading whitespace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            (workspace / "data" / "cron-runs").mkdir(parents=True, exist_ok=True)
            (workspace / "data" / "cron-runs" / "2026-04-01.jsonl").write_text(
                json.dumps(
                    {
                        "job": "alpha-polymarket",
                        "agent": "alpha",
                        "ts": "2026-04-01T10:10:00Z",
                        "status": "ok",
                        "summary": "orchestrator ok",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (workspace / "data" / "alpha" / "research").mkdir(parents=True, exist_ok=True)
            ar_path = workspace / "data" / "alpha" / "research" / "2026-04-01-10.md"
            ar_path.write_text("# alpha\n", encoding="utf-8")
            alpha_epoch = datetime.strptime("2026-04-01T10:12:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
            os.utime(ar_path, (alpha_epoch, alpha_epoch))
            (workspace / "data" / "agent-reports").mkdir(parents=True, exist_ok=True)
            (workspace / "data" / "agent-reports" / "2026-04-01.json").write_text(
                json.dumps(
                    {
                        "reports": [
                            {
                                "agent": "alpha",
                                "job": "alpha-polymarket",
                                "timestamp": "2026-04-01T10:11:00Z",
                                "summary": "hold",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (workspace / "data" / "audit-log").mkdir(parents=True, exist_ok=True)
            (workspace / "data" / "audit-log" / "2026-04-01.jsonl").write_text(
                json.dumps(
                    {
                        "ts": "2026-04-01T10:12:00Z",
                        "kind": "telegram_post",
                        "topic": "polymarket",
                        "message": "\n  Alpha · Hourly · HOLD — no edge this hour; gates applied  \n",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            paperclip = [
                {
                    "id": "issue-alpha",
                    "title": "[alpha-polymarket] 2026-04-01 10:00 UTC",
                    "status": "done",
                    "updatedAt": "2026-04-01T10:12:00Z",
                },
            ]
            paperclip_file = workspace / "paperclip-issues.json"
            paperclip_file.write_text(json.dumps(paperclip), encoding="utf-8")
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["WORKFLOW_HEALTH_NOW"] = "2026-04-01T10:30:00Z"
            env["WORKFLOW_HEALTH_PAPERCLIP_ISSUES_FILE"] = str(paperclip_file)
            result = subprocess.run(
                ["python3", str(self.script), "audit-one", "alpha-polymarket", "--include-paperclip"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            report = json.loads(result.stdout)
            self.assertTrue(report["healthy"], msg=report)

        with tempfile.TemporaryDirectory() as tmpdir2:
            workspace = Path(tmpdir2)
            self._seed_core_jobs(workspace)
            (workspace / "data" / "cron-runs").mkdir(parents=True, exist_ok=True)
            (workspace / "data" / "cron-runs" / "2026-04-01.jsonl").write_text(
                json.dumps(
                    {
                        "job": "alpha-polymarket",
                        "agent": "alpha",
                        "ts": "2026-04-01T10:10:00Z",
                        "status": "ok",
                        "summary": "ok",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (workspace / "data" / "alpha" / "research").mkdir(parents=True, exist_ok=True)
            ar_path2 = workspace / "data" / "alpha" / "research" / "2026-04-01-10.md"
            ar_path2.write_text("# alpha\n", encoding="utf-8")
            os.utime(ar_path2, (alpha_epoch, alpha_epoch))
            (workspace / "data" / "agent-reports").mkdir(parents=True, exist_ok=True)
            (workspace / "data" / "agent-reports" / "2026-04-01.json").write_text(
                json.dumps(
                    {
                        "reports": [
                            {
                                "agent": "alpha",
                                "job": "alpha-polymarket",
                                "timestamp": "2026-04-01T10:11:00Z",
                                "summary": "trade",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (workspace / "data" / "audit-log").mkdir(parents=True, exist_ok=True)
            (workspace / "data" / "audit-log" / "2026-04-01.jsonl").write_text(
                json.dumps(
                    {
                        "ts": "2026-04-01T10:12:00Z",
                        "kind": "telegram_post",
                        "topic": "polymarket",
                        "message": "Alpha (hourly): TRADE — small edge on inflation print.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            paperclip_file2 = workspace / "paperclip-issues.json"
            paperclip_file2.write_text(json.dumps(paperclip), encoding="utf-8")
            env2 = os.environ.copy()
            env2["WORKSPACE_ROOT"] = str(workspace)
            env2["WORKFLOW_HEALTH_NOW"] = "2026-04-01T10:30:00Z"
            env2["WORKFLOW_HEALTH_PAPERCLIP_ISSUES_FILE"] = str(paperclip_file2)
            result2 = subprocess.run(
                ["python3", str(self.script), "audit-one", "alpha-polymarket", "--include-paperclip"],
                cwd=str(self.workspace),
                env=env2,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result2.returncode, 0, msg=result2.stderr or result2.stdout)
            report2 = json.loads(result2.stdout)
            self.assertTrue(report2["healthy"], msg=report2)


if __name__ == "__main__":
    unittest.main()

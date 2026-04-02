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
                {"id": "4", "name": "kimi-polymarket", "schedule": {"kind": "cron", "expr": "0 * * * *"}, "payload": {}, "delivery": {}, "agentId": "kimi"},
            ]
        }
        for path in [workspace / "cron" / "jobs.json", workspace / ".openclaw" / "cron" / "jobs.json"]:
            path.write_text(json.dumps(jobs), encoding="utf-8")

    def _seed_full_evidence(self, workspace: Path, alpha_ts: str, kimi_ts: str, research_ts: str, brief_ts: str) -> list[dict]:
        (workspace / "data" / "cron-runs").mkdir(parents=True, exist_ok=True)
        (workspace / "data" / "alpha" / "research").mkdir(parents=True, exist_ok=True)
        (workspace / "data" / "kimi" / "research").mkdir(parents=True, exist_ok=True)
        (workspace / "data" / "research" / "openclaw").mkdir(parents=True, exist_ok=True)
        (workspace / "data" / "agent-reports").mkdir(parents=True, exist_ok=True)
        (workspace / "data" / "audit-log").mkdir(parents=True, exist_ok=True)

        (workspace / "data" / "cron-runs" / "2026-04-01.jsonl").write_text(
            "\n".join(
                [
                    json.dumps({"job": "grok-daily-brief", "agent": "grok", "ts": brief_ts, "status": "ok", "summary": "posted brief"}),
                    json.dumps({"job": "grok-openclaw-research", "agent": "grok", "ts": research_ts, "status": "ok", "summary": "saved research"}),
                    json.dumps({"job": "alpha-polymarket", "agent": "alpha", "ts": alpha_ts, "status": "ok", "summary": "alpha summary"}),
                    json.dumps({"job": "kimi-polymarket", "agent": "kimi", "ts": kimi_ts, "status": "ok", "summary": "kimi summary"}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (workspace / "data" / "research" / "openclaw" / "2026-04-01.md").write_text("# research\n", encoding="utf-8")
        (workspace / "data" / "alpha" / "research" / "2026-04-01.md").write_text("# alpha\n", encoding="utf-8")
        (workspace / "data" / "kimi" / "research" / "2026-04-01.md").write_text("# kimi\n", encoding="utf-8")
        research_epoch = datetime.strptime(research_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
        alpha_epoch = datetime.strptime(alpha_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
        kimi_epoch = datetime.strptime(kimi_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
        os.utime(workspace / "data" / "research" / "openclaw" / "2026-04-01.md", (research_epoch, research_epoch))
        os.utime(workspace / "data" / "alpha" / "research" / "2026-04-01.md", (alpha_epoch, alpha_epoch))
        os.utime(workspace / "data" / "kimi" / "research" / "2026-04-01.md", (kimi_epoch, kimi_epoch))

        (workspace / "data" / "agent-reports" / "2026-04-01.json").write_text(
            json.dumps(
                {
                    "reports": [
                        {"agent": "alpha", "job": "alpha-polymarket", "timestamp": alpha_ts, "summary": "alpha summary"},
                        {"agent": "kimi", "job": "kimi-polymarket", "timestamp": kimi_ts, "summary": "kimi summary"},
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
                    json.dumps({"ts": kimi_ts, "kind": "telegram_post", "topic": "polymarket", "message": "Kimi session: skip. Why: no edge."}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return [
            {"id": "issue-daily", "title": "[grok-daily-brief] 2026-04-01 08:00 UTC", "status": "done", "updatedAt": "2026-04-01T08:06:00Z"},
            {"id": "issue-research", "title": "[grok-openclaw-research] 2026-04-01 07:00 UTC", "status": "done", "updatedAt": research_ts},
            {"id": "issue-alpha", "title": "[alpha-polymarket] 2026-04-01 09:00 UTC", "status": "done", "updatedAt": alpha_ts},
            {"id": "issue-kimi", "title": "[kimi-polymarket] 2026-04-01 09:00 UTC", "status": "done", "updatedAt": kimi_ts},
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
                    {"id": "4", "name": "kimi-polymarket", "schedule": {"kind": "cron", "expr": "0 * * * *"}, "payload": {}, "delivery": {}, "agentId": "kimi"},
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
                        json.dumps(
                            {
                                "job": "kimi-polymarket",
                                "agent": "kimi",
                                "ts": "2026-04-01T10:08:00Z",
                                "status": "ok",
                                "summary": "skipped with rationale",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (workspace / "data" / "research" / "openclaw").mkdir(parents=True)
            (workspace / "data" / "kimi" / "research").mkdir(parents=True)
            (workspace / "data" / "research" / "openclaw" / "2026-04-01-morning.md").write_text("# research\n", encoding="utf-8")
            (workspace / "data" / "alpha" / "research" / "2026-04-01-10.md").write_text("# alpha run\n", encoding="utf-8")
            (workspace / "data" / "kimi" / "research" / "2026-04-01-10.md").write_text("# kimi run\n", encoding="utf-8")
            openclaw_epoch = datetime.strptime("2026-04-01T07:06:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
            alpha_epoch = datetime.strptime("2026-04-01T10:12:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
            kimi_epoch = datetime.strptime("2026-04-01T10:09:30Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
            os.utime(workspace / "data" / "research" / "openclaw" / "2026-04-01-morning.md", (openclaw_epoch, openclaw_epoch))
            os.utime(workspace / "data" / "alpha" / "research" / "2026-04-01-10.md", (alpha_epoch, alpha_epoch))
            os.utime(workspace / "data" / "kimi" / "research" / "2026-04-01-10.md", (kimi_epoch, kimi_epoch))
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
                            {
                                "agent": "kimi",
                                "job": "kimi-polymarket",
                                "timestamp": "2026-04-01T10:09:00Z",
                                "summary": "skipped with rationale",
                            }
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
                        json.dumps(
                            {
                                "ts": "2026-04-01T10:09:30Z",
                                "kind": "telegram_post",
                                "topic": "polymarket",
                                "message": "Kimi session: skip. Why: no edge.",
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
                {
                    "id": "issue-2",
                    "title": "[kimi-polymarket] 2026-04-01 10:00 UTC",
                    "status": "done",
                    "updatedAt": "2026-04-01T10:09:30Z",
                }
            ]

            report = self._run_audit(workspace, "2026-04-01T10:30:00Z", payload)
            self.assertTrue(report["healthy"])
            self.assertEqual(report["failures"], [])

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
                    {"id": "4", "name": "kimi-polymarket", "schedule": {"kind": "cron", "expr": "0 * * * *"}, "payload": {}, "delivery": {}, "agentId": "kimi"},
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
                    "status": "done",
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
                kimi_ts="2026-04-01T09:09:00Z",
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
                kimi_ts="2026-04-01T12:09:00Z",
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
                kimi_ts="2026-04-01T10:09:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )

            report = self._run_audit(workspace, "2026-04-01T10:30:00Z", payload)
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("alpha-polymarket", messages)

    def test_kimi_requires_the_latest_expected_run_after_grace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T10:10:00Z",
                kimi_ts="2026-04-01T09:09:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )

            report = self._run_audit(workspace, "2026-04-01T10:30:00Z", payload)
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("kimi-polymarket", messages)

    def test_daily_brief_happy_path_satisfies_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T08:10:00Z",
                kimi_ts="2026-04-01T08:09:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )

            report = self._run_audit(workspace, "2026-04-01T08:30:00Z", payload)
            self.assertTrue(report["healthy"])

    def test_daily_brief_sad_path_flags_missing_audit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T08:10:00Z",
                kimi_ts="2026-04-01T08:09:00Z",
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
                kimi_ts="2026-04-01T13:09:00Z",
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
                kimi_ts="2026-04-01T13:09:00Z",
                research_ts="2026-04-01T13:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )
            (workspace / "data" / "research" / "openclaw" / "2026-04-01.md").unlink()

            report = self._run_audit(workspace, "2026-04-01T13:30:00Z", payload)
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("grok-openclaw-research is missing research markdown", messages)

    def test_alpha_happy_path_satisfies_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T10:10:00Z",
                kimi_ts="2026-04-01T10:09:00Z",
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
                kimi_ts="2026-04-01T10:09:00Z",
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

    def test_kimi_happy_path_satisfies_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T10:10:00Z",
                kimi_ts="2026-04-01T10:09:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )

            report = self._run_audit(workspace, "2026-04-01T10:30:00Z", payload)
            self.assertTrue(report["healthy"])

    def test_kimi_sad_path_flags_missing_paperclip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            payload = self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T10:10:00Z",
                kimi_ts="2026-04-01T10:09:00Z",
                research_ts="2026-04-01T07:06:00Z",
                brief_ts="2026-04-01T08:05:00Z",
            )
            payload = [issue for issue in payload if not issue["title"].startswith("[kimi-polymarket]")]

            report = self._run_audit(workspace, "2026-04-01T10:30:00Z", payload)
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("kimi-polymarket is missing a recent Paperclip issue", messages)

    def test_audit_one_uses_local_evidence_for_single_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._seed_core_jobs(workspace)
            self._seed_full_evidence(
                workspace,
                alpha_ts="2026-04-01T10:10:00Z",
                kimi_ts="2026-04-01T10:09:00Z",
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
                "2026-04-01T14:00:00Z",
                "audit-quick",
            )
            self.assertFalse(report["healthy"])
            messages = "\n".join(failure["message"] for failure in report["failures"])
            self.assertIn("kimi-polymarket", messages)


if __name__ == "__main__":
    unittest.main()

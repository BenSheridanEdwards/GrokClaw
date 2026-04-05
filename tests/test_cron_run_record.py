import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class CronRunRecordTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "cron-run-record.sh"

    def _write_stub(self, path: Path, body: str) -> None:
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def _setup_workspace_tools(self, workspace: Path) -> tuple[Path, Path, Path]:
        tools_dir = workspace / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        lifecycle_log = workspace / "lifecycle.log"
        telegram_log = workspace / "telegram.log"
        paperclip_log = workspace / "paperclip.log"

        self._write_stub(
            tools_dir / "cron-paperclip-lifecycle.sh",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                set -eu
                printf '%s\\n' "$*" >> "{lifecycle_log}"
                """
            ),
        )
        self._write_stub(
            tools_dir / "telegram-post.sh",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                set -eu
                printf '%s\\n' "$*" >> "{telegram_log}"
                """
            ),
        )
        self._write_stub(
            tools_dir / "paperclip-api.sh",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                set -eu
                printf '%s\\n' "$*" >> "{paperclip_log}"
                """
            ),
        )
        return lifecycle_log, telegram_log, paperclip_log

    def test_records_json_and_finishes_paperclip_issue(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            lifecycle_log, telegram_log, _ = self._setup_workspace_tools(workspace)
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PAPERCLIP_ISSUE_UUID"] = "issue-123"

            result = subprocess.run(
                ["sh", str(self.script), "alpha-polymarket", "alpha", "ok", "placed one trade"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            today_file = next((workspace / "data" / "cron-runs").glob("*.jsonl"))
            record = json.loads(today_file.read_text(encoding="utf-8").strip())
            self.assertEqual(record["job"], "alpha-polymarket")
            self.assertEqual(record["agent"], "alpha")
            self.assertEqual(record["status"], "ok")
            self.assertEqual(record["summary"], "placed one trade")

            self.assertEqual(
                lifecycle_log.read_text(encoding="utf-8").strip(),
                "finish issue-123 ok placed one trade",
            )
            self.assertFalse(telegram_log.exists(), "successful runs should not post routine health confirmations")

    def test_started_run_records_without_finishing_paperclip_or_auditing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            lifecycle_log, telegram_log, _ = self._setup_workspace_tools(workspace)
            audit_log = workspace / "audit.log"
            handler_log = workspace / "handler.log"

            self._write_stub(
                workspace / "tools" / "_workflow_health.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import sys
                    with open("{audit_log}", "a", encoding="utf-8") as handle:
                        handle.write(" ".join(sys.argv[1:]) + "\\n")
                    """
                ),
            )
            self._write_stub(
                workspace / "tools" / "_workflow_health_handle.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import sys
                    with open("{handler_log}", "a", encoding="utf-8") as handle:
                        handle.write(sys.stdin.read())
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PAPERCLIP_ISSUE_UUID"] = "issue-123"

            result = subprocess.run(
                ["sh", str(self.script), "alpha-polymarket", "alpha", "started", "run started"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            today_file = next((workspace / "data" / "cron-runs").glob("*.jsonl"))
            record = json.loads(today_file.read_text(encoding="utf-8").strip())
            self.assertEqual(record["status"], "started")
            self.assertFalse(lifecycle_log.exists(), "started runs should not close Paperclip yet")
            self.assertFalse(telegram_log.exists(), "started runs should not post health alerts")
            self.assertFalse(audit_log.exists(), "started runs should not audit completion yet")
            self.assertFalse(handler_log.exists(), "started runs should not call the health handler")

    def test_skipped_run_closes_issue_as_ok(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            lifecycle_log, _, _ = self._setup_workspace_tools(workspace)
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PAPERCLIP_ISSUE_UUID"] = "issue-123"

            result = subprocess.run(
                ["sh", str(self.script), "grok-openclaw-research", "grok", "skipped", "nothing new to report"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertEqual(
                lifecycle_log.read_text(encoding="utf-8").strip(),
                "finish issue-123 skipped nothing new to report",
            )
            self.assertFalse((workspace / "telegram.log").exists(), "skipped runs should not post routine health confirmations")

    def test_error_run_adds_detailed_paperclip_comment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            lifecycle_log, telegram_log, paperclip_log = self._setup_workspace_tools(workspace)
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PAPERCLIP_ISSUE_UUID"] = "issue-123"
            env["CRON_ERROR_DETAILS"] = "Traceback: market validation failed"

            result = subprocess.run(
                ["sh", str(self.script), "kimi-polymarket", "kimi", "error", "trade loop failed"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertEqual(
                lifecycle_log.read_text(encoding="utf-8").strip(),
                "finish issue-123 error trade loop failed",
            )
            self.assertEqual(
                telegram_log.read_text(encoding="utf-8").strip(),
                "health [kimi] kimi-polymarket: error -- trade loop failed",
            )
            self.assertIn("comment issue-123 Error details:", paperclip_log.read_text(encoding="utf-8"))
            self.assertIn("Traceback: market validation failed", paperclip_log.read_text(encoding="utf-8"))

    def test_error_still_finishes_if_telegram_post_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            lifecycle_log, telegram_log, _ = self._setup_workspace_tools(workspace)
            self._write_stub(
                workspace / "tools" / "telegram-post.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{telegram_log}"
                    exit 1
                    """
                ),
            )
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PAPERCLIP_ISSUE_UUID"] = "issue-123"

            result = subprocess.run(
                ["sh", str(self.script), "alpha-polymarket", "alpha", "error", "placed one trade"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(
                lifecycle_log.read_text(encoding="utf-8").strip(),
                "finish issue-123 error placed one trade",
            )

    def test_resolves_issue_uuid_from_openclaw_job_file_when_env_unset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            lifecycle_log, _, _ = self._setup_workspace_tools(workspace)
            oc = workspace / ".openclaw"
            oc.mkdir(parents=True)
            (oc / "kimi-polymarket.issue").write_text("issue-from-file\n", encoding="utf-8")
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env.pop("PAPERCLIP_ISSUE_UUID", None)

            result = subprocess.run(
                ["sh", str(self.script), "kimi-polymarket", "kimi", "ok", "session complete"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertEqual(
                lifecycle_log.read_text(encoding="utf-8").strip(),
                "finish issue-from-file ok session complete",
            )


    def test_env_var_takes_precedence_over_issue_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            lifecycle_log, _, _ = self._setup_workspace_tools(workspace)

            issue_dir = workspace / ".openclaw"
            issue_dir.mkdir(parents=True, exist_ok=True)
            (issue_dir / "alpha-polymarket.issue").write_text("issue-from-file")

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PAPERCLIP_ISSUE_UUID"] = "issue-from-env"

            result = subprocess.run(
                ["sh", str(self.script), "alpha-polymarket", "alpha", "ok", "trade placed"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertEqual(
                lifecycle_log.read_text(encoding="utf-8").strip(),
                "finish issue-from-env ok trade placed",
            )

    def test_no_env_var_and_no_issue_file_skips_paperclip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            lifecycle_log, _, _ = self._setup_workspace_tools(workspace)

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env.pop("PAPERCLIP_ISSUE_UUID", None)

            result = subprocess.run(
                ["sh", str(self.script), "alpha-polymarket", "alpha", "ok", "no paperclip"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertFalse(lifecycle_log.exists(), "lifecycle should not run when no UUID is available")

    def test_runs_audit_one_and_hands_payload_to_handler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._setup_workspace_tools(workspace)
            audit_log = workspace / "audit.log"
            handler_log = workspace / "handler.log"

            self._write_stub(
                workspace / "tools" / "_workflow_health.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import json, sys
                    with open("{audit_log}", "a", encoding="utf-8") as handle:
                        handle.write(" ".join(sys.argv[1:]) + "\\n")
                    print(json.dumps({{
                        "healthy": False,
                        "failureHash": "abc123",
                        "alertMessage": "Workflow health failure: alpha missing research markdown",
                        "draft": {{
                            "id": "workflow-health-abc123",
                            "title": "Fix workflow health failure in core cron workflows",
                            "description": "Problem and acceptance criteria"
                        }}
                    }}))
                    """
                ),
            )
            self._write_stub(
                workspace / "tools" / "_workflow_health_handle.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import sys
                    with open("{handler_log}", "a", encoding="utf-8") as handle:
                        handle.write(sys.stdin.read())
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                ["sh", str(self.script), "alpha-polymarket", "alpha", "ok", "placed one trade"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(audit_log.exists(), "cron-run-record should invoke workflow audit")
            self.assertIn("audit-one alpha-polymarket --include-paperclip", audit_log.read_text(encoding="utf-8"))
            self.assertTrue(handler_log.exists(), "cron-run-record should hand audit payload to the handler")
            self.assertIn('"failureHash": "abc123"', handler_log.read_text(encoding="utf-8"))

    def test_error_run_defers_to_workflow_health_handler_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            _, telegram_log, _ = self._setup_workspace_tools(workspace)
            audit_log = workspace / "audit.log"
            handler_log = workspace / "handler.log"

            self._write_stub(
                workspace / "tools" / "_workflow_health.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import json, sys
                    with open("{audit_log}", "a", encoding="utf-8") as handle:
                        handle.write(" ".join(sys.argv[1:]) + "\\n")
                    print(json.dumps({{
                        "healthy": False,
                        "failureHash": "err123",
                        "alertMessage": "Workflow health failure: kimi error",
                        "draft": None
                    }}))
                    """
                ),
            )
            self._write_stub(
                workspace / "tools" / "_workflow_health_handle.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import sys
                    with open("{handler_log}", "a", encoding="utf-8") as handle:
                        handle.write(sys.stdin.read())
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                ["sh", str(self.script), "kimi-polymarket", "kimi", "error", "trade loop failed"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("audit-one kimi-polymarket --include-paperclip", audit_log.read_text(encoding="utf-8"))
            self.assertIn('"failureHash": "err123"', handler_log.read_text(encoding="utf-8"))
            self.assertFalse(telegram_log.exists(), "direct telegram alert should be skipped when the workflow health handler is active")


if __name__ == "__main__":
    unittest.main()

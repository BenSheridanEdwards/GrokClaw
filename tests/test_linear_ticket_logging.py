import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class LinearTicketLoggingTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "linear-ticket.sh"

    def _write_stub_linear_helper(self, workspace: Path) -> None:
        tools_dir = workspace / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        helper = tools_dir / "_linear_ticket.py"
        helper.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                print("https://linear.app/grokclaw/issue/GRO-42/test-ticket")
                """
            ),
            encoding="utf-8",
        )
        helper.chmod(0o755)

    def _write_pending_draft(
        self,
        workspace: Path,
        *,
        draft_id: str = "suggestion-12",
        flow: str = "suggestion",
        reference_id: str = "12",
        title: str = "Improve cron workflows",
        description: str = "Full description",
    ) -> None:
        data_dir = workspace / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        pending = data_dir / f"pending-linear-draft-{draft_id}.json"
        pending.write_text(
            json.dumps(
                {
                    "flow": flow,
                    "referenceId": reference_id,
                    "topic": "suggestions",
                    "title": title,
                    "description": description,
                    "transitionTo": "In Progress",
                }
            ),
            encoding="utf-8",
        )

    def test_logs_successful_linear_creation_with_flow_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._write_stub_linear_helper(workspace)
            self._write_pending_draft(workspace)
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["LINEAR_API_KEY"] = "test-key"
            env["LINEAR_CREATION_FLOW"] = "suggestion"
            env["LINEAR_DRAFT_ID"] = "suggestion-12"
            env["OPENCLAW_AGENT_ID"] = "grok"

            result = subprocess.run(
                ["sh", str(self.script), "12", "Improve cron workflows", "Full description"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("https://linear.app/grokclaw/issue/GRO-42/test-ticket", result.stdout)

            log_file = next((workspace / "data" / "linear-creations").glob("*.jsonl"))
            record = json.loads(log_file.read_text(encoding="utf-8").strip())
            self.assertEqual(record["flow"], "suggestion")
            self.assertEqual(record["referenceId"], "12")
            self.assertEqual(record["title"], "Improve cron workflows")
            self.assertEqual(record["url"], "https://linear.app/grokclaw/issue/GRO-42/test-ticket")
            self.assertEqual(record["agent"], "grok")

    def test_rejects_missing_linear_creation_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._write_stub_linear_helper(workspace)
            self._write_pending_draft(workspace)
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["LINEAR_API_KEY"] = "test-key"
            env["LINEAR_DRAFT_ID"] = "suggestion-12"

            result = subprocess.run(
                ["sh", str(self.script), "12", "Improve cron workflows", "Full description"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("LINEAR_CREATION_FLOW", result.stderr)

    def test_rejects_missing_approved_draft(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._write_stub_linear_helper(workspace)
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["LINEAR_API_KEY"] = "test-key"
            env["LINEAR_CREATION_FLOW"] = "suggestion"

            result = subprocess.run(
                ["sh", str(self.script), "12", "Improve cron workflows", "Full description"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("LINEAR_DRAFT_ID", result.stderr)

    def test_rejects_when_args_do_not_match_approved_draft(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._write_stub_linear_helper(workspace)
            self._write_pending_draft(workspace)
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["LINEAR_API_KEY"] = "test-key"
            env["LINEAR_CREATION_FLOW"] = "suggestion"
            env["LINEAR_DRAFT_ID"] = "suggestion-12"

            result = subprocess.run(
                ["sh", str(self.script), "12", "Different title", "Full description"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("approved draft", result.stderr)


if __name__ == "__main__":
    unittest.main()

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class WorkflowHealthHandleTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "_workflow_health_handle.py"

    def _write_executable(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def _run_handler(self, workspace: Path, payload: dict, state_file: Path) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["WORKSPACE_ROOT"] = str(workspace)
        env["WORKFLOW_HEALTH_STATE_FILE"] = str(state_file)
        return subprocess.run(
            ["python3", str(self.script)],
            cwd=str(self.workspace),
            env=env,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_new_failure_posts_alert_and_requests_draft(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            health_log = workspace / "health.log"
            draft_log = workspace / "draft.log"
            state_file = workspace / "state.json"

            self._write_executable(
                workspace / "tools" / "telegram-post.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{health_log}"
                    """
                ),
            )
            self._write_executable(
                workspace / "tools" / "linear-draft-approval.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{draft_log}"
                    """
                ),
            )

            payload = {
                "healthy": False,
                "failureHash": "abc123",
                "alertMessage": "Workflow health failure: alpha missing research markdown",
                "draft": {
                    "id": "workflow-health-abc123",
                    "title": "Fix workflow health failure in core cron workflows",
                    "description": "Problem and acceptance criteria",
                },
            }

            result = self._run_handler(workspace, payload, state_file)
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("health Workflow health failure: alpha missing research markdown", health_log.read_text(encoding="utf-8"))
            self.assertIn(
                "request workflow-health-abc123 suggestion abc123 suggestions Fix workflow health failure in core cron workflows Problem and acceptance criteria In Progress",
                draft_log.read_text(encoding="utf-8"),
            )
            saved = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(saved["hash"], "abc123")
            self.assertEqual(saved["status"], "open")

    def test_same_failure_hash_does_not_re_request_draft(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            health_log = workspace / "health.log"
            draft_log = workspace / "draft.log"
            state_file = workspace / "state.json"

            self._write_executable(
                workspace / "tools" / "telegram-post.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{health_log}"
                    """
                ),
            )
            self._write_executable(
                workspace / "tools" / "linear-draft-approval.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{draft_log}"
                    """
                ),
            )
            state_file.write_text(json.dumps({"hash": "samehash", "status": "open"}), encoding="utf-8")

            payload = {
                "healthy": False,
                "failureHash": "samehash",
                "alertMessage": "Workflow health failure: repeated",
                "draft": {
                    "id": "workflow-health-samehash",
                    "title": "Fix workflow health failure in core cron workflows",
                    "description": "Problem and acceptance criteria",
                },
            }

            result = self._run_handler(workspace, payload, state_file)
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertFalse(health_log.exists())
            self.assertFalse(draft_log.exists())

    def test_healthy_payload_marks_state_resolved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            state_file = workspace / "state.json"
            state_file.write_text(json.dumps({"hash": "oldhash", "status": "open"}), encoding="utf-8")

            payload = {
                "healthy": True,
                "failureHash": "healthy",
                "alertMessage": "Workflow health: healthy",
                "draft": None,
            }

            result = self._run_handler(workspace, payload, state_file)
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            saved = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "resolved")


if __name__ == "__main__":
    unittest.main()

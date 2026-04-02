import datetime as dt
import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path
from typing import Dict, Optional


class WorkflowHealthHandleTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "_workflow_health_handle.py"

    def _write_executable(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def _run_handler(
        self,
        workspace: Path,
        payload: dict,
        state_file: Path,
        extra_env: Optional[Dict[str, str]] = None,
    ) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["WORKSPACE_ROOT"] = str(workspace)
        env["WORKFLOW_HEALTH_STATE_FILE"] = str(state_file)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["python3", str(self.script)],
            cwd=str(self.workspace),
            env=env,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )

    def _stub_telegram_tools(self, workspace, health_log, inline_log=None):
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
        log_target = inline_log or health_log
        self._write_executable(
            workspace / "tools" / "telegram-inline.sh",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                set -eu
                printf '%s\\n' "$*" >> "{log_target}"
                """
            ),
        )
        self._write_executable(
            workspace / "tools" / "retry.sh",
            textwrap.dedent(
                """\
                #!/bin/sh
                set -eu
                while [ "$#" -gt 0 ]; do
                  case "$1" in
                    --) shift; break ;;
                    *) shift ;;
                  esac
                done
                exec "$@"
                """
            ),
        )

    def test_new_failure_posts_alert_and_requests_draft(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            health_log = workspace / "health.log"
            inline_log = workspace / "inline.log"
            draft_log = workspace / "draft.log"
            state_file = workspace / "state.json"

            self._stub_telegram_tools(workspace, health_log, inline_log)
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
                "failures": [
                    {"workflow": "alpha-polymarket", "kind": "missing_research", "message": "no research markdown"},
                ],
                "alertMessage": "alpha-polymarket: no research file written\n\nthe agent ran but didn't write output — check the prompt",
                "draft": {
                    "id": "workflow-health-abc123",
                    "title": "Fix workflow health failure in core cron workflows",
                    "description": "Problem and acceptance criteria",
                },
            }

            result = self._run_handler(workspace, payload, state_file)
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(inline_log.exists(), "alert with rerun button should use telegram-inline.sh")
            inline_text = inline_log.read_text(encoding="utf-8")
            self.assertIn("Rerun alpha-polymarket", inline_text)
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

            self._stub_telegram_tools(workspace, health_log)
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
            failures = [{"workflow": "grok-daily-brief", "kind": "stale_run", "message": "stale at 08:00"}]
            import hashlib
            struct_hash = hashlib.sha256(
                json.dumps(sorted({(f["workflow"], f["kind"]) for f in failures}), sort_keys=True).encode()
            ).hexdigest()[:12]
            today = dt.datetime.utcnow().strftime("%Y-%m-%d")

            state_file.write_text(json.dumps({
                "hash": "samehash",
                "structHash": struct_hash,
                "status": "open",
                "last_seen": f"{today}T00:00:00Z",
            }), encoding="utf-8")

            payload = {
                "healthy": False,
                "failureHash": "samehash",
                "failures": failures,
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

    def test_pending_workflow_health_draft_blocks_duplicate_request(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            health_log = workspace / "health.log"
            draft_log = workspace / "draft.log"
            state_file = workspace / "state.json"
            (workspace / "data").mkdir(parents=True, exist_ok=True)
            (workspace / "data" / "pending-linear-draft-workflow-health-old.json").write_text(
                json.dumps(
                    {
                        "flow": "suggestion",
                        "title": "Fix workflow health failure in core cron workflows",
                        "description": "Existing draft",
                    }
                ),
                encoding="utf-8",
            )

            self._stub_telegram_tools(workspace, health_log)
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
                "failureHash": "newhash",
                "alertMessage": "Workflow health failure: repeated class",
                "draft": {
                    "id": "workflow-health-newhash",
                    "title": "Fix workflow health failure in core cron workflows",
                    "description": "Problem and acceptance criteria",
                },
            }

            result = self._run_handler(workspace, payload, state_file)
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(health_log.exists(), "health alert should still be posted")
            self.assertFalse(draft_log.exists(), "duplicate pending draft should suppress new draft request")

    def test_open_linear_match_blocks_duplicate_request(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            health_log = workspace / "health.log"
            draft_log = workspace / "draft.log"
            state_file = workspace / "state.json"
            open_linear_file = workspace / "open-linear.json"
            open_linear_file.write_text(
                json.dumps(["Fix workflow health failure in core cron workflows"]),
                encoding="utf-8",
            )

            self._stub_telegram_tools(workspace, health_log)
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
                "failureHash": "openlinearhash",
                "alertMessage": "Workflow health failure: repeated class",
                "draft": {
                    "id": "workflow-health-openlinearhash",
                    "title": "Fix workflow health failure in core cron workflows",
                    "description": "Problem and acceptance criteria",
                },
            }

            result = self._run_handler(
                workspace,
                payload,
                state_file,
                {"WORKFLOW_HEALTH_OPEN_LINEAR_TITLES_FILE": str(open_linear_file)},
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(health_log.exists(), "health alert should still be posted")
            self.assertFalse(draft_log.exists(), "open Linear match should suppress new draft request")

    def test_open_pr_match_blocks_duplicate_request(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            health_log = workspace / "health.log"
            draft_log = workspace / "draft.log"
            state_file = workspace / "state.json"
            open_pr_file = workspace / "open-prs.json"
            open_pr_file.write_text(
                json.dumps(["Fix workflow health failure in core cron workflows"]),
                encoding="utf-8",
            )

            self._stub_telegram_tools(workspace, health_log)
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
                "failureHash": "openprhash",
                "alertMessage": "Workflow health failure: repeated class",
                "draft": {
                    "id": "workflow-health-openprhash",
                    "title": "Fix workflow health failure in core cron workflows",
                    "description": "Problem and acceptance criteria",
                },
            }

            result = self._run_handler(
                workspace,
                payload,
                state_file,
                {"WORKFLOW_HEALTH_OPEN_PR_TITLES_FILE": str(open_pr_file)},
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(health_log.exists(), "health alert should still be posted")
            self.assertFalse(draft_log.exists(), "open PR match should suppress new draft request")


if __name__ == "__main__":
    unittest.main()

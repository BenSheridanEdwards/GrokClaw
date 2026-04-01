import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class CronPaperclipLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.script = self.repo_root / "tools" / "cron-paperclip-lifecycle.sh"

    def _write_stub_api(self, workspace: Path) -> Path:
        tools_dir = workspace / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        log_path = workspace / "paperclip-api.log"
        stub_path = tools_dir / "paperclip-api.sh"
        stub_path.write_text(
            textwrap.dedent(
                f"""\
                #!/bin/sh
                set -eu
                printf '%s\\n' "$*" >> "{log_path}"
                case "$1" in
                  create-issue)
                    echo "Created: PAP-101 - $2"
                    echo "ID: issue-uuid-123"
                    ;;
                  update-issue)
                    printf '{{"id":"%s","status":"%s"}}\\n' "$2" "$3"
                    ;;
                  comment)
                    printf '{{"id":"%s","body":"%s"}}\\n' "$2" "$3"
                    ;;
                  *)
                    echo "unexpected command: $1" >&2
                    exit 1
                    ;;
                esac
                """
            ),
            encoding="utf-8",
        )
        stub_path.chmod(0o755)
        return log_path

    def test_start_creates_issue_and_marks_it_in_progress(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            log_path = self._write_stub_api(workspace)
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["CRON_PAPERCLIP_NOW"] = "2026-04-01T08:00:00Z"

            result = subprocess.run(
                ["sh", str(self.script), "start", "alpha-polymarket", "alpha"],
                cwd=str(self.repo_root),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertEqual(result.stdout.strip(), "issue-uuid-123")

            calls = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(calls), 2)
            self.assertIn("create-issue", calls[0])
            self.assertIn("[alpha-polymarket] 2026-04-01 08:00 UTC", calls[0])
            self.assertIn("update-issue issue-uuid-123 in_progress", calls[1])

    def test_finish_marks_issue_done_and_comments_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            log_path = self._write_stub_api(workspace)
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["CRON_PAPERCLIP_NOW"] = "2026-04-01T08:00:00Z"

            result = subprocess.run(
                ["sh", str(self.script), "finish", "issue-uuid-123", "ok", "posted daily brief"],
                cwd=str(self.repo_root),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            calls = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(calls[0], "update-issue issue-uuid-123 done")
            self.assertIn("comment issue-uuid-123 [2026-04-01 08:00 UTC] ok -- posted daily brief", calls[1])

    def test_finish_marks_issue_failed_on_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            log_path = self._write_stub_api(workspace)
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["CRON_PAPERCLIP_NOW"] = "2026-04-01T08:00:00Z"

            result = subprocess.run(
                ["sh", str(self.script), "finish", "issue-uuid-123", "error", "trade validation failed"],
                cwd=str(self.repo_root),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            calls = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(calls[0], "update-issue issue-uuid-123 failed")
            self.assertIn("comment issue-uuid-123 [2026-04-01 08:00 UTC] error -- trade validation failed", calls[1])

    def test_finish_marks_issue_cancelled_on_skip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            log_path = self._write_stub_api(workspace)
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["CRON_PAPERCLIP_NOW"] = "2026-04-01T08:00:00Z"

            result = subprocess.run(
                ["sh", str(self.script), "finish", "issue-uuid-123", "skipped", "no candidate market found"],
                cwd=str(self.repo_root),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            calls = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(calls[0], "update-issue issue-uuid-123 cancelled")
            self.assertIn("comment issue-uuid-123 [2026-04-01 08:00 UTC] skipped -- no candidate market found", calls[1])

    def test_start_refuses_non_core_job(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._write_stub_api(workspace)
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                ["sh", str(self.script), "start", "changelog-weekly-check", "grok"],
                cwd=str(self.repo_root),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-core", result.stderr)


if __name__ == "__main__":
    unittest.main()

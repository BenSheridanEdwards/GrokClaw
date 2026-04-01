import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class PreCommitHookTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.hook = self.workspace / ".githooks" / "pre-commit"
        self.runner = self.workspace / "tools" / "run-health-e2e-tests.sh"

    def _write_executable(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_repo_managed_pre_commit_hook_runs_health_e2e_runner(self):
        self.assertTrue(self.hook.exists(), "expected repo-managed pre-commit hook")
        content = self.hook.read_text(encoding="utf-8")
        self.assertIn("tools/run-health-e2e-tests.sh", content)

    def test_health_e2e_runner_invokes_expected_suite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            bin_dir = tmp / "bin"
            call_log = tmp / "python.log"

            self._write_executable(
                bin_dir / "python3",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{call_log}"
                    exit 0
                    """
                ),
            )

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"

            result = subprocess.run(
                ["sh", str(self.runner)],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            invoked = call_log.read_text(encoding="utf-8")
            self.assertIn("-m unittest", invoked)
            self.assertIn("tests.test_workflow_health", invoked)
            self.assertIn("tests.test_grokclaw_doctor", invoked)
            self.assertIn("tests.test_health_check", invoked)
            self.assertIn("tests.test_gateway_watchdog", invoked)
            self.assertIn("tests.test_health_schedules", invoked)
            self.assertIn("tests.test_cron_paperclip_lifecycle", invoked)
            self.assertIn("tests.test_telegram_audit_log", invoked)


if __name__ == "__main__":
    unittest.main()

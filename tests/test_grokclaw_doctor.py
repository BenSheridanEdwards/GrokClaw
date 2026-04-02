import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class GrokClawDoctorTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "grokclaw-doctor.sh"

    def _write_executable(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def _build_doctor_workspace(self, tmp: Path, *, audit_exit: int = 1, audit_output: str = "alpha-polymarket missing research markdown"):
        """Set up a temp workspace with stubs for all doctor external deps."""
        home = tmp / "home"
        workspace = tmp / "workspace"
        tools_dir = workspace / "tools"
        stubs_bin = tmp / "stubs"
        health_log = workspace / "health.log"

        self._write_executable(
            tools_dir / "telegram-post.sh",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                set -eu
                printf '%s\\n' "$*" >> "{health_log}"
                """
            ),
        )
        self._write_executable(
            tools_dir / "cron-jobs-tool.py",
            "#!/usr/bin/env python3\nimport sys; sys.exit(0)\n",
        )
        self._write_executable(
            tools_dir / "_workflow_health_audit.py",
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import sys
                msg = '''{audit_output}'''
                if msg:
                    print(msg)
                sys.exit({audit_exit})
                """
            ),
        )
        self._write_executable(
            tools_dir / "gateway-ctl.sh",
            "#!/bin/sh\nexit 0\n",
        )
        self._write_executable(
            tools_dir / "sync-cron-jobs.sh",
            "#!/bin/sh\nexit 0\n",
        )

        stubs_bin.mkdir(parents=True, exist_ok=True)
        self._write_executable(
            stubs_bin / "curl",
            "#!/bin/sh\nexit 0\n",
        )
        self._write_executable(
            stubs_bin / "launchctl",
            textwrap.dedent(
                """\
                #!/bin/sh
                echo "com.grokclaw.gateway"
                echo "com.grokclaw.paperclip"
                """
            ),
        )
        self._write_executable(
            stubs_bin / "crontab",
            '#!/bin/sh\necho "*/5 * * * * health-check.sh"\n',
        )
        self._write_executable(
            stubs_bin / "openclaw",
            "#!/bin/sh\nexit 0\n",
        )

        cron_dir = workspace / "cron"
        cron_dir.mkdir(parents=True, exist_ok=True)
        (cron_dir / "jobs.json").write_text('{"jobs":[]}', encoding="utf-8")
        rt_dir = home / ".openclaw" / "cron"
        rt_dir.mkdir(parents=True, exist_ok=True)
        (rt_dir / "jobs.json").write_text('{"jobs":[]}', encoding="utf-8")

        return home, workspace, health_log, stubs_bin

    def test_doctor_alerts_on_workflow_health_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            home, workspace, health_log, stubs_bin = self._build_doctor_workspace(
                tmp,
                audit_exit=1,
                audit_output="alpha-polymarket missing research markdown",
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{stubs_bin}:{env.get('PATH', '')}"
            env["TELEGRAM_BOT_TOKEN"] = "test-token"

            result = subprocess.run(
                ["sh", str(self.script), "--check"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1, msg=result.stderr or result.stdout)
            alert_text = health_log.read_text(encoding="utf-8")
            self.assertIn("GrokClaw Doctor", alert_text)
            self.assertIn("Workflow health: alpha-polymarket missing research markdown", alert_text)

    def test_doctor_healthy_when_audit_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            home, workspace, health_log, stubs_bin = self._build_doctor_workspace(
                tmp,
                audit_exit=0,
                audit_output="",
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{stubs_bin}:{env.get('PATH', '')}"
            env["TELEGRAM_BOT_TOKEN"] = "test-token"

            result = subprocess.run(
                ["sh", str(self.script), "--check"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("All checks passed", result.stdout)
            self.assertFalse(
                health_log.exists(),
                "No Telegram alert when all checks pass",
            )


if __name__ == "__main__":
    unittest.main()

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class HealthCheckTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "health-check.sh"

    def _write_executable(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_dead_gateway_hands_off_to_watchdog_without_direct_alert(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            bin_dir = workspace / "bin"
            handoff_log = workspace / "watchdog.log"
            alert_log = workspace / "health.log"

            self._write_executable(bin_dir / "curl", "#!/bin/sh\nset -eu\nexit 1\n")
            self._write_executable(
                tools_dir / "telegram-poller-guard.sh",
                "#!/bin/sh\nset -eu\nexit 0\n",
            )
            self._write_executable(
                tools_dir / "gateway-watchdog.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{handoff_log}"
                    exit 0
                    """
                ),
            )
            self._write_executable(
                tools_dir / "telegram-post.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{alert_log}"
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{bin_dir}:{env['PATH']}"

            result = subprocess.run(
                ["sh", str(self.script)],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertTrue(handoff_log.exists(), "health-check should invoke gateway-watchdog.sh on failure")
            self.assertIn("health-check", handoff_log.read_text(encoding="utf-8"))
            self.assertFalse(alert_log.exists(), "health-check should hand off repair instead of alerting directly")

    def test_dead_gateway_alerts_when_watchdog_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            bin_dir = workspace / "bin"
            alert_log = workspace / "health.log"

            self._write_executable(bin_dir / "curl", "#!/bin/sh\nset -eu\nexit 1\n")
            self._write_executable(
                tools_dir / "telegram-poller-guard.sh",
                "#!/bin/sh\nset -eu\nexit 0\n",
            )
            self._write_executable(
                tools_dir / "telegram-post.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{alert_log}"
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{bin_dir}:{env['PATH']}"

            result = subprocess.run(
                ["sh", str(self.script)],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertTrue(alert_log.exists(), "health-check should alert when watchdog handoff is unavailable")
            self.assertIn("health", alert_log.read_text(encoding="utf-8"))

    def test_dead_gateway_alerts_when_watchdog_handoff_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            bin_dir = workspace / "bin"
            handoff_log = workspace / "watchdog.log"
            alert_log = workspace / "health.log"

            self._write_executable(bin_dir / "curl", "#!/bin/sh\nset -eu\nexit 1\n")
            self._write_executable(
                tools_dir / "telegram-poller-guard.sh",
                "#!/bin/sh\nset -eu\nexit 0\n",
            )
            self._write_executable(
                tools_dir / "gateway-watchdog.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{handoff_log}"
                    exit 1
                    """
                ),
            )
            self._write_executable(
                tools_dir / "telegram-post.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{alert_log}"
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{bin_dir}:{env['PATH']}"

            result = subprocess.run(
                ["sh", str(self.script)],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertTrue(handoff_log.exists(), "health-check should attempt watchdog handoff first")
            self.assertTrue(alert_log.exists(), "health-check should alert when the watchdog command errors")


if __name__ == "__main__":
    unittest.main()

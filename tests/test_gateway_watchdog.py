import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class GatewayWatchdogTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "gateway-watchdog.sh"

    def _write_executable(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_unhealthy_gateway_attempts_repair_and_stays_quiet_when_it_recovers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            bin_dir = workspace / "bin"
            health_log = workspace / "health.log"
            restart_log = workspace / "restart.log"
            sync_log = workspace / "sync.log"
            curl_state = workspace / "curl-state"

            self._write_executable(
                bin_dir / "curl",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    count=0
                    if [ -f "{curl_state}" ]; then
                      count="$(cat "{curl_state}")"
                    fi
                    count=$((count + 1))
                    printf '%s\\n' "$count" > "{curl_state}"
                    if [ "$count" -eq 1 ]; then
                      exit 1
                    fi
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
                    printf '%s\\n' "$*" >> "{health_log}"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "gateway-ctl.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{restart_log}"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "sync-cron-jobs.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{sync_log}"
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

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(restart_log.exists(), "watchdog should attempt a gateway restart when health is bad")
            self.assertIn("restart", restart_log.read_text(encoding="utf-8"))
            self.assertTrue(sync_log.exists(), "watchdog should refresh runtime dependencies during repair")
            self.assertFalse(health_log.exists(), "successful self-repair should stay quiet")

    def test_unhealthy_gateway_alerts_after_exhausting_repair(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            bin_dir = workspace / "bin"
            health_log = workspace / "health.log"
            restart_log = workspace / "restart.log"

            self._write_executable(bin_dir / "curl", "#!/bin/sh\nset -eu\nexit 1\n")
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
                tools_dir / "gateway-ctl.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{restart_log}"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "sync-cron-jobs.sh",
                "#!/bin/sh\nset -eu\nexit 0\n",
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

            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(restart_log.exists(), "watchdog should attempt repair before alerting")
            self.assertIn("restart", restart_log.read_text(encoding="utf-8"))
            self.assertIn("health Gateway watchdog:", health_log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

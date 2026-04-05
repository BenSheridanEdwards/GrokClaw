import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class RunOpenClawAgentTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "run-openclaw-agent.sh"

    def _write_executable(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_passes_timeout_flag_through_to_openclaw(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            bin_dir = temp_root / "bin"
            argv_log = temp_root / "argv.log"
            self._write_executable(
                bin_dir / "openclaw",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{argv_log}"
                    exit 0
                    """
                ),
            )

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
            env["OPENCLAW_AGENT_TIMEOUT_SECONDS"] = "900"
            env["OPENCLAW_MESSAGE"] = "test message"
            env["PAPERCLIP_WORKSPACE_CWD"] = str(self.workspace)

            result = subprocess.run(
                ["bash", str(self.script)],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("--timeout 900", argv_log.read_text(encoding="utf-8"))

    def test_retries_once_after_openclaw_failure_when_configured(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            bin_dir = temp_root / "bin"
            attempts_log = temp_root / "attempts.log"
            state_file = temp_root / "attempt-state"
            self._write_executable(
                bin_dir / "openclaw",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    count=0
                    if [ -f "{state_file}" ]; then
                      count=$(cat "{state_file}")
                    fi
                    count=$((count + 1))
                    printf '%s' "$count" > "{state_file}"
                    printf 'attempt %s: %s\\n' "$count" "$*" >> "{attempts_log}"
                    if [ "$count" -lt 2 ]; then
                      exit 1
                    fi
                    exit 0
                    """
                ),
            )

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
            env["OPENCLAW_AGENT_RETRIES"] = "1"
            env["OPENCLAW_MESSAGE"] = "test message"
            env["PAPERCLIP_WORKSPACE_CWD"] = str(self.workspace)

            result = subprocess.run(
                ["bash", str(self.script)],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            attempts = attempts_log.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(attempts), 2)


if __name__ == "__main__":
    unittest.main()

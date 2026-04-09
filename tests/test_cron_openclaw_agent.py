import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class CronOpenclawAgentTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]
        self.script = self.repo / "tools" / "_cron_openclaw_agent.py"

    def _write(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_retries_once_and_emits_failure_telemetry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            prompt = tmp / "prompt.md"
            prompt.write_text("run alpha turn", encoding="utf-8")
            counter = tmp / "counter.txt"
            telemetry = tmp / "telemetry.jsonl"
            fake_openclaw = tmp / "bin" / "openclaw"
            self._write(
                fake_openclaw,
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    count="$(cat "{counter}" 2>/dev/null || echo 0)"
                    count=$((count + 1))
                    printf '%s' "$count" > "{counter}"
                    if [ "$count" -eq 1 ]; then
                      echo "provider timeout on first attempt" >&2
                      exit 1
                    fi
                    echo "ok on retry"
                    exit 0
                    """
                ),
            )

            env = os.environ.copy()
            env["OPENCLAW_BIN"] = str(fake_openclaw)

            result = subprocess.run(
                [
                    "python3",
                    str(self.script),
                    str(prompt),
                    "--agent",
                    "alpha",
                    "--session-id",
                    "session-123",
                    "--timeout",
                    "10",
                    "--retries",
                    "1",
                    "--retry-backoff",
                    "0",
                    "--telemetry-file",
                    str(telemetry),
                    "--cwd",
                    str(tmp),
                ],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("ok on retry", result.stdout)
            self.assertTrue(telemetry.exists(), "retry failure should be logged")
            rows = [json.loads(line) for line in telemetry.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["attempt"], 1)
            self.assertEqual(rows[0]["maxAttempts"], 2)
            self.assertEqual(rows[0]["reason"], "timeout")

    def test_returns_last_failure_when_retries_exhausted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            prompt = tmp / "prompt.md"
            prompt.write_text("run alpha turn", encoding="utf-8")
            telemetry = tmp / "telemetry.jsonl"
            fake_openclaw = tmp / "bin" / "openclaw"
            self._write(
                fake_openclaw,
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    echo "rate limit reached" >&2
                    exit 1
                    """
                ),
            )

            env = os.environ.copy()
            env["OPENCLAW_BIN"] = str(fake_openclaw)

            result = subprocess.run(
                [
                    "python3",
                    str(self.script),
                    str(prompt),
                    "--agent",
                    "alpha",
                    "--session-id",
                    "session-999",
                    "--timeout",
                    "10",
                    "--retries",
                    "1",
                    "--retry-backoff",
                    "0",
                    "--telemetry-file",
                    str(telemetry),
                    "--cwd",
                    str(tmp),
                ],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            rows = [json.loads(line) for line in telemetry.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["reason"], "rate_limit")
            self.assertEqual(rows[1]["reason"], "rate_limit")


if __name__ == "__main__":
    unittest.main()

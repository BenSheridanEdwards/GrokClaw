import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class PrReviewWatchTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "pr-review-watch.sh"

    def _write_executable(self, path: Path, body: str) -> None:
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_wakes_grok_when_review_queue_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / "home"
            workspace = Path(tmpdir) / "workspace"
            tools_dir = workspace / "tools"
            bin_dir = workspace / "bin"
            state_dir = home / ".openclaw" / "state"
            tools_dir.mkdir(parents=True, exist_ok=True)
            bin_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)

            gh_output = workspace / "gh-output.json"
            gh_log = workspace / "gh.log"
            wake_log = workspace / "wake.log"
            gh_output.write_text('[{"number":12,"title":"Example PR","url":"https://example/pr/12"}]\n', encoding="utf-8")

            self._write_executable(
                bin_dir / "gh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{gh_log}"
                    cat "{gh_output}"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "run-openclaw-agent.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "__WAKE__" >> "{wake_log}"
                    printf '%s\\n' "${{OPENCLAW_MESSAGE:-}}" >> "{wake_log}"
                    """
                ),
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{bin_dir}:{env['PATH']}"

            first = subprocess.run(
                ["sh", str(self.script)],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, msg=first.stderr or first.stdout)
            self.assertIn("--label needs-grok-review", gh_log.read_text(encoding="utf-8"))
            self.assertIn("Queued pull requests:", wake_log.read_text(encoding="utf-8"))
            self.assertIn("#12 Example PR", wake_log.read_text(encoding="utf-8"))

            second = subprocess.run(
                ["sh", str(self.script)],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(second.returncode, 0, msg=second.stderr or second.stdout)
            self.assertEqual(wake_log.read_text(encoding="utf-8").count("__WAKE__"), 1)

            gh_output.write_text('[{"number":15,"title":"Second PR","url":"https://example/pr/15"}]\n', encoding="utf-8")
            third = subprocess.run(
                ["sh", str(self.script)],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(third.returncode, 0, msg=third.stderr or third.stdout)
            self.assertEqual(wake_log.read_text(encoding="utf-8").count("__WAKE__"), 2)

    def test_clears_state_when_queue_is_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / "home"
            workspace = Path(tmpdir) / "workspace"
            tools_dir = workspace / "tools"
            bin_dir = workspace / "bin"
            state_dir = home / ".openclaw" / "state"
            tools_dir.mkdir(parents=True, exist_ok=True)
            bin_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)

            gh_output = workspace / "gh-output.json"
            wake_log = workspace / "wake.log"
            gh_output.write_text("[]\n", encoding="utf-8")

            self._write_executable(
                bin_dir / "gh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    cat "{gh_output}"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "run-openclaw-agent.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "__WAKE__" >> "{wake_log}"
                    printf '%s\\n' "${{OPENCLAW_MESSAGE:-}}" >> "{wake_log}"
                    """
                ),
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
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
            self.assertFalse(wake_log.exists(), "empty review queues should not wake Grok")
            self.assertFalse((state_dir / "pr-review-watch.last").exists(), "empty review queues should not leave stale state")


if __name__ == "__main__":
    unittest.main()

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class DispatchActionLinearDraftTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "dispatch-telegram-action.sh"

    def _write_executable(self, path: Path, body: str) -> None:
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_approve_linear_draft_marks_seen_on_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / "home"
            workspace = Path(tmpdir) / "workspace"
            tools_dir = workspace / "tools"
            state_dir = home / ".openclaw" / "state"
            tools_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)

            self._write_executable(
                tools_dir / "linear-draft-approval.sh",
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    exit 0
                    """
                ),
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                ["sh", str(self.script), "Create | approve_linear_draft:suggestion-8"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            seen_file = state_dir / "telegram-action-seen.txt"
            self.assertIn("approve_linear_draft:suggestion-8", seen_file.read_text(encoding="utf-8"))

    def test_reject_linear_draft_marks_seen_on_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / "home"
            workspace = Path(tmpdir) / "workspace"
            tools_dir = workspace / "tools"
            state_dir = home / ".openclaw" / "state"
            tools_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)

            self._write_executable(
                tools_dir / "linear-draft-approval.sh",
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    exit 0
                    """
                ),
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                ["sh", str(self.script), "Cancel | reject_linear_draft:suggestion-8"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            seen_file = state_dir / "telegram-action-seen.txt"
            self.assertIn("reject_linear_draft:suggestion-8", seen_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

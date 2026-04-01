import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class LinearDraftApprovalTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "linear-draft-approval.sh"

    def _write_executable(self, path: Path, body: str) -> None:
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_request_writes_pending_draft_and_posts_inline_buttons(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            tools_dir.mkdir(parents=True, exist_ok=True)
            telegram_log = workspace / "telegram-inline.log"

            self._write_executable(
                tools_dir / "telegram-inline.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{telegram_log}"
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                [
                    "sh",
                    str(self.script),
                    "request",
                    "suggestion-8",
                    "suggestion",
                    "8",
                    "suggestions",
                    "Improve Grok brief",
                    "Detailed draft body",
                    "In Progress",
                ],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            pending = workspace / "data" / "pending-linear-draft-suggestion-8.json"
            self.assertTrue(pending.exists())
            record = json.loads(pending.read_text(encoding="utf-8"))
            self.assertEqual(record["flow"], "suggestion")
            self.assertEqual(record["referenceId"], "8")
            self.assertEqual(record["transitionTo"], "In Progress")

            telegram = telegram_log.read_text(encoding="utf-8")
            self.assertIn("approve_linear_draft:suggestion-8", telegram)
            self.assertIn("reject_linear_draft:suggestion-8", telegram)
            self.assertIn("Improve Grok brief", telegram)

    def test_create_suggestion_draft_creates_linear_and_transitions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            data_dir = workspace / "data"
            tools_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)
            post_log = workspace / "telegram-post.log"
            transition_log = workspace / "linear-transition.log"

            pending = data_dir / "pending-linear-draft-suggestion-8.json"
            pending.write_text(
                json.dumps(
                    {
                        "flow": "suggestion",
                        "referenceId": "8",
                        "topic": "suggestions",
                        "title": "Improve Grok brief",
                        "description": "Detailed draft body",
                        "transitionTo": "In Progress",
                    }
                ),
                encoding="utf-8",
            )

            self._write_executable(
                tools_dir / "linear-ticket.sh",
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    printf '%s|%s\n' "${LINEAR_CREATION_FLOW:-}" "${LINEAR_DRAFT_ID:-}" > "$WORKSPACE_ROOT/flow.log"
                    echo "https://linear.app/grokclaw/issue/GRO-42/test-ticket"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "linear-transition.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{transition_log}"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "telegram-post.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{post_log}"
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                ["sh", str(self.script), "create", "suggestion-8"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertFalse(pending.exists(), "pending draft should be removed after creation")
            self.assertEqual((workspace / "flow.log").read_text(encoding="utf-8").strip(), "suggestion|suggestion-8")
            self.assertEqual(transition_log.read_text(encoding="utf-8").strip(), "GRO-42 In Progress")
            self.assertIn("https://linear.app/grokclaw/issue/GRO-42/test-ticket", post_log.read_text(encoding="utf-8"))

    def test_create_user_request_draft_skips_linear_transition(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            data_dir = workspace / "data"
            tools_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)
            post_log = workspace / "telegram-post.log"
            transition_log = workspace / "linear-transition.log"

            pending = data_dir / "pending-linear-draft-user-req-1.json"
            pending.write_text(
                json.dumps(
                    {
                        "flow": "user_request",
                        "referenceId": "telegram-1",
                        "topic": "suggestions",
                        "title": "Fix webhook retry issue",
                        "description": "Detailed draft body",
                        "transitionTo": "",
                    }
                ),
                encoding="utf-8",
            )

            self._write_executable(
                tools_dir / "linear-ticket.sh",
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    echo "https://linear.app/grokclaw/issue/GRO-77/test-ticket"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "linear-transition.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{transition_log}"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "telegram-post.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{post_log}"
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                ["sh", str(self.script), "create", "user-req-1"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertFalse(transition_log.exists(), "user-request flow should not auto-transition Linear")
            self.assertIn("GRO-77", post_log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

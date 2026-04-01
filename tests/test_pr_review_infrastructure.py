import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class PrReviewInfrastructureTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.handler = self.workspace / "tools" / "pr-review-handler.sh"
        self.workflow = self.workspace / ".github" / "workflows" / "pr-review.yml"

    def _write_executable(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_workflow_marks_pull_requests_for_grok_review(self):
        content = self.workflow.read_text(encoding="utf-8")
        self.assertIn("pull_request_target:", content)
        self.assertIn("opened", content)
        self.assertIn("ready_for_review", content)
        self.assertIn("synchronize", content)
        self.assertIn("if: ${{ !github.event.pull_request.draft }}", content)
        self.assertIn("pull-requests: write", content)
        self.assertIn("needs-grok-review", content)
        self.assertIn("grok-approved", content)
        self.assertIn("<!-- grokclaw-pr-review-request -->", content)

    def test_list_shows_labelled_review_queue(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            bin_dir = tmp / "bin"
            gh_log = tmp / "gh.log"
            queue_json = tmp / "queue.json"
            queue_json.write_text(
                '[{"number":12,"title":"Example PR","url":"https://example/pr/12","headRefName":"grok/GRO-31","isDraft":false}]\n',
                encoding="utf-8",
            )

            self._write_executable(
                bin_dir / "gh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{gh_log}"
                    cat "{queue_json}"
                    """
                ),
            )

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"

            result = subprocess.run(
                ["sh", str(self.handler), "list"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("--label needs-grok-review", gh_log.read_text(encoding="utf-8"))
            self.assertIn("#12 Example PR", result.stdout)
            self.assertIn("grok/GRO-31", result.stdout)

    def test_approve_reviews_transitions_and_notifies(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            workspace = tmp / "workspace"
            tools_dir = workspace / "tools"
            bin_dir = tmp / "bin"
            gh_log = tmp / "gh.log"
            telegram_log = tmp / "telegram.log"
            linear_log = tmp / "linear.log"
            view_json = tmp / "view.json"
            view_json.write_text(
                '{"number":12,"title":"Implement GRO-31","url":"https://example/pr/12","headRefName":"grok/GRO-31"}\n',
                encoding="utf-8",
            )

            self._write_executable(
                bin_dir / "gh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{gh_log}"
                    if [ "${{1:-}}" = "pr" ] && [ "${{2:-}}" = "view" ]; then
                      cat "{view_json}"
                    fi
                    """
                ),
            )
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
            self._write_executable(
                tools_dir / "linear-transition.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s|%s\\n' "$1" "$2" >> "{linear_log}"
                    """
                ),
            )

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                [
                    "sh",
                    str(self.handler),
                    "approve",
                    "12",
                    "GRO-31",
                    "Ready for Ben to merge.",
                    "Spec reviewed and approved.",
                ],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            gh_calls = gh_log.read_text(encoding="utf-8")
            self.assertIn("pr review 12 --repo BenSheridanEdwards/GrokClaw --approve --body Spec reviewed and approved.", gh_calls)
            self.assertIn("pr edit 12 --repo BenSheridanEdwards/GrokClaw --remove-label needs-grok-review --add-label grok-approved", gh_calls)
            self.assertIn("GRO-31|In Review", linear_log.read_text(encoding="utf-8"))

            telegram_text = telegram_log.read_text(encoding="utf-8")
            self.assertIn("pr-reviews", telegram_text)
            self.assertIn("Ready for Ben to merge.", telegram_text)
            self.assertIn("merge:12:GRO-31", telegram_text)
            self.assertIn("reject:12:GRO-31", telegram_text)
            self.assertIn("https://linear.app/grokclaw/issue/GRO-31", telegram_text)

    def test_request_changes_stays_quiet_on_telegram(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            workspace = tmp / "workspace"
            tools_dir = workspace / "tools"
            bin_dir = tmp / "bin"
            gh_log = tmp / "gh.log"
            telegram_log = tmp / "telegram.log"

            self._write_executable(
                bin_dir / "gh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{gh_log}"
                    """
                ),
            )
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
            self._write_executable(
                tools_dir / "linear-transition.sh",
                "#!/bin/sh\nset -eu\n",
            )

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                [
                    "sh",
                    str(self.handler),
                    "request-changes",
                    "12",
                    "Please address the review comments.",
                ],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            gh_calls = gh_log.read_text(encoding="utf-8")
            self.assertIn("pr review 12 --repo BenSheridanEdwards/GrokClaw --request-changes --body Please address the review comments.", gh_calls)
            self.assertIn("pr edit 12 --repo BenSheridanEdwards/GrokClaw --remove-label grok-approved --remove-label needs-grok-review", gh_calls)
            self.assertFalse(telegram_log.exists(), "request-changes should not notify Telegram")


if __name__ == "__main__":
    unittest.main()

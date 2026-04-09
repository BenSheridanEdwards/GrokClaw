import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class GrokOpenclawResearchDeterministicTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]
        self.script = self.repo / "tools" / "_grok_openclaw_research_deterministic.py"

    def _write_stub(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_deterministic_research_writes_slot_file_and_posts_headline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            bin_dir = workspace / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            audit_log = workspace / "data" / "audit-log" / "2026-04-09.jsonl"

            self._write_stub(bin_dir / "openclaw", "#!/bin/sh\nset -eu\necho 'openclaw v2026.4.9'\n")
            self._write_stub(bin_dir / "npm", "#!/bin/sh\nset -eu\necho '2026.4.9'\n")
            self._write_stub(
                bin_dir / "gh",
                "#!/bin/sh\nset -eu\necho '{\"tagName\":\"v2026.4.9\",\"publishedAt\":\"2026-04-09T02:25:00Z\"}'\n",
            )
            self._write_stub(
                workspace / "tools" / "telegram-post.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    mkdir -p "{audit_log.parent}"
                    printf '{{"ts":"2026-04-09T07:00:10Z","kind":"telegram_post","topic":"%s","message":"%s"}}\\n' "$1" "$2" >> "{audit_log}"
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
            env["GROK_RESEARCH_NOW"] = "2026-04-09T07:00:00Z"
            env["CRON_RUN_ID"] = "research-det-test"
            result = subprocess.run(
                ["python3", str(self.script), str(workspace)],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            payload = json.loads(result.stdout.strip())
            self.assertEqual(payload["slot"], "morning")
            self.assertEqual(payload["telegramPostCode"], 0)

            research = workspace / "data" / "research" / "openclaw" / "2026-04-09-morning.md"
            self.assertTrue(research.exists())
            content = research.read_text(encoding="utf-8")
            self.assertIn("## Latest stable", content)
            self.assertIn("openclaw v2026.4.9", content)
            self.assertTrue(audit_log.exists())
            self.assertIn("OpenClaw research (morning):", audit_log.read_text(encoding="utf-8"))

    def test_deterministic_research_survives_cli_failures(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            bin_dir = workspace / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)

            self._write_stub(bin_dir / "openclaw", "#!/bin/sh\nset -eu\nexit 1\n")
            self._write_stub(bin_dir / "npm", "#!/bin/sh\nset -eu\nexit 1\n")
            self._write_stub(bin_dir / "gh", "#!/bin/sh\nset -eu\nexit 1\n")
            self._write_stub(workspace / "tools" / "telegram-post.sh", "#!/bin/sh\nset -eu\nexit 1\n")

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
            env["GROK_RESEARCH_NOW"] = "2026-04-09T13:00:00Z"
            result = subprocess.run(
                ["python3", str(self.script), str(workspace)],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout.strip())
            self.assertEqual(payload["slot"], "afternoon")
            self.assertEqual(payload["localVersion"], "unknown")
            self.assertEqual(payload["npmVersion"], "unknown")
            self.assertEqual(payload["githubLatest"], "unknown")

            research = workspace / "data" / "research" / "openclaw" / "2026-04-09-afternoon.md"
            self.assertTrue(research.exists())


if __name__ == "__main__":
    unittest.main()

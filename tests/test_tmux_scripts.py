"""Tests for tmux skill helper scripts (dry-run mode, no tmux required)."""
import subprocess
import unittest
from pathlib import Path


class TmuxScriptDryRunTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.find_sessions = self.workspace / "skills" / "tmux" / "scripts" / "find-sessions.sh"
        self.wait_for_text = self.workspace / "skills" / "tmux" / "scripts" / "wait-for-text.sh"

    def test_find_sessions_dry_run_default_socket(self):
        result = subprocess.run(
            ["bash", str(self.find_sessions), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        out = result.stdout + result.stderr
        self.assertIn("[dry-run]", out)
        self.assertIn("default", out)

    def test_find_sessions_dry_run_all_sockets(self):
        result = subprocess.run(
            ["bash", str(self.find_sessions), "--dry-run", "--all"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("all sockets", result.stdout)

    def test_find_sessions_dry_run_rejects_conflicting_flags(self):
        result = subprocess.run(
            [
                "bash",
                str(self.find_sessions),
                "--dry-run",
                "-L",
                "foo",
                "--all",
            ],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertNotEqual(result.returncode, 0)

    def test_wait_for_text_dry_run(self):
        result = subprocess.run(
            [
                "bash",
                str(self.wait_for_text),
                "--dry-run",
                "-t",
                "s:0.0",
                "-p",
                "ready",
                "-T",
                "5",
            ],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        out = result.stdout + result.stderr
        self.assertIn("s:0.0", out)
        self.assertIn("ready", out)
        self.assertIn("timeout=5s", out)

    def test_wait_for_text_dry_run_invalid_timeout_still_fails(self):
        result = subprocess.run(
            [
                "bash",
                str(self.wait_for_text),
                "--dry-run",
                "-t",
                "s:0.0",
                "-p",
                "x",
                "-T",
                "notint",
            ],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertNotEqual(result.returncode, 0)

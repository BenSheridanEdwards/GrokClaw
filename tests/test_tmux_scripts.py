"""Tests for tmux helper scripts (find-sessions.sh, wait-for-text.sh)."""
import subprocess
import unittest
from pathlib import Path


class TmuxScriptsTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.skills_tmux = self.workspace / "skills" / "tmux" / "scripts"
        self.find_sessions = self.skills_tmux / "find-sessions.sh"
        self.wait_for_text = self.skills_tmux / "wait-for-text.sh"

    def _run(self, script, args, expect_ok=True):
        result = subprocess.run(
            ["bash", str(script)] + args,
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        if expect_ok:
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return result

    def test_find_sessions_help_exits_zero(self):
        """find-sessions.sh --help exits 0."""
        self._run(self.find_sessions, ["--help"])

    def test_find_sessions_help_shows_usage(self):
        """find-sessions.sh --help shows usage and options."""
        r = self._run(self.find_sessions, ["--help"])
        out = r.stdout + r.stderr
        self.assertIn("Usage:", out)
        self.assertIn("-L", out)
        self.assertIn("-S", out)
        self.assertIn("-A", out)
        self.assertIn("-q", out)

    def test_find_sessions_invalid_option_exits_one(self):
        """find-sessions.sh with unknown option exits 1."""
        result = subprocess.run(
            ["bash", str(self.find_sessions), "--unknown"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown option", result.stderr or result.stdout)

    def test_find_sessions_l_and_s_together_exits_one(self):
        """find-sessions.sh -L and -S together exits 1."""
        result = subprocess.run(
            ["bash", str(self.find_sessions), "-L", "foo", "-S", "/tmp/bar"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("either -L or -S", result.stderr or result.stdout)

    def test_find_sessions_all_with_l_exits_one(self):
        """find-sessions.sh --all with -L exits 1."""
        result = subprocess.run(
            ["bash", str(self.find_sessions), "-A", "-L", "foo"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cannot combine", result.stderr or result.stdout)

    def test_wait_for_text_help_exits_zero(self):
        """wait-for-text.sh --help exits 0."""
        self._run(self.wait_for_text, ["--help"])

    def test_wait_for_text_help_shows_usage(self):
        """wait-for-text.sh --help shows usage and options."""
        r = self._run(self.wait_for_text, ["--help"])
        out = r.stdout + r.stderr
        self.assertIn("Usage:", out)
        self.assertIn("-t", out)
        self.assertIn("-p", out)
        self.assertIn("-T", out)

    def test_wait_for_text_missing_target_exits_one(self):
        """wait-for-text.sh without -t exits 1."""
        result = subprocess.run(
            ["bash", str(self.wait_for_text), "-p", "foo"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("target and pattern are required", result.stderr or result.stdout)

    def test_wait_for_text_missing_pattern_exits_one(self):
        """wait-for-text.sh without -p exits 1."""
        result = subprocess.run(
            ["bash", str(self.wait_for_text), "-t", "session:0.0"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("target and pattern are required", result.stderr or result.stdout)

    def test_wait_for_text_invalid_timeout_exits_one(self):
        """wait-for-text.sh with non-integer timeout exits 1."""
        result = subprocess.run(
            ["bash", str(self.wait_for_text), "-t", "x:0.0", "-p", "x", "-T", "abc"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("timeout must be an integer", result.stderr or result.stdout)

    def test_wait_for_text_invalid_option_exits_one(self):
        """wait-for-text.sh with unknown option exits 1."""
        result = subprocess.run(
            ["bash", str(self.wait_for_text), "--unknown"],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown option", result.stderr or result.stdout)

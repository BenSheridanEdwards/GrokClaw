"""Tests for tmux skill helper scripts (find-sessions.sh, wait-for-text.sh)."""
import os
import subprocess
import unittest
from pathlib import Path


class TmuxScriptsTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.find_sessions = self.workspace / "skills" / "tmux" / "scripts" / "find-sessions.sh"
        self.wait_for_text = self.workspace / "skills" / "tmux" / "scripts" / "wait-for-text.sh"

    def _run(self, script, args, env=None):
        env = env or os.environ.copy()
        return subprocess.run(
            [str(script)] + args,
            env=env,
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )

    def test_find_sessions_help_exits_zero(self):
        """find-sessions.sh -h exits 0 and prints usage."""
        r = self._run(self.find_sessions, ["-h"])
        self.assertEqual(r.returncode, 0, msg=r.stderr or r.stdout)
        self.assertIn("Usage:", r.stdout)
        self.assertIn("find-sessions.sh", r.stdout)

    def test_find_sessions_invalid_option_exits_one(self):
        """find-sessions.sh exits 1 for unknown option."""
        r = self._run(self.find_sessions, ["--unknown"])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Unknown option", r.stderr or r.stdout)

    def test_find_sessions_conflicting_options_exits_one(self):
        """find-sessions.sh exits 1 when combining --all with -L or -S."""
        r = self._run(self.find_sessions, ["-A", "-L", "x"])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Cannot combine", r.stderr or r.stdout)

    def test_find_sessions_both_socket_options_exits_one(self):
        """find-sessions.sh exits 1 when using both -L and -S."""
        r = self._run(self.find_sessions, ["-L", "a", "-S", "/tmp/x"])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Use either -L or -S", r.stderr or r.stdout)

    def test_wait_for_text_help_exits_zero(self):
        """wait-for-text.sh -h exits 0 and prints usage."""
        r = self._run(self.wait_for_text, ["-h"])
        self.assertEqual(r.returncode, 0, msg=r.stderr or r.stdout)
        self.assertIn("Usage:", r.stdout)
        self.assertIn("wait-for-text.sh", r.stdout)

    def test_wait_for_text_missing_args_exits_one(self):
        """wait-for-text.sh exits 1 when target and pattern are missing."""
        r = self._run(self.wait_for_text, [])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("target and pattern are required", r.stderr or r.stdout)

    def test_wait_for_text_invalid_timeout_exits_one(self):
        """wait-for-text.sh exits 1 when timeout is not an integer."""
        r = self._run(self.wait_for_text, ["-t", "x:0.0", "-p", "y", "-T", "abc"])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("timeout must be an integer", r.stderr or r.stdout)

    def test_wait_for_text_invalid_lines_exits_one(self):
        """wait-for-text.sh exits 1 when lines is not an integer."""
        r = self._run(self.wait_for_text, ["-t", "x:0.0", "-p", "y", "-l", "nope"])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("lines must be an integer", r.stderr or r.stdout)


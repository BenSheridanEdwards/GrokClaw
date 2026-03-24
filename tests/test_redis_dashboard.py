"""Tests for tools/redis-dashboard.sh."""
import os
import subprocess
import unittest
from pathlib import Path


class RedisDashboardTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "redis-dashboard.sh"

    def test_dry_run_exits_zero(self):
        """Dry run should exit 0 whether Redis is available or not."""
        result = subprocess.run(
            ["sh", str(self.script), "--dry-run"],
            env={**os.environ, "WORKSPACE_ROOT": str(self.workspace)},
            cwd=str(self.workspace),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")

    def test_dry_run_prints_skip_or_report(self):
        """Dry run prints skip message (no redis-cli) or report content."""
        result = subprocess.run(
            ["sh", str(self.script), "--dry-run"],
            env={**os.environ, "WORKSPACE_ROOT": str(self.workspace)},
            cwd=str(self.workspace),
            capture_output=True,
            text=True,
        )
        out = result.stdout + result.stderr
        # Either skips (redis-cli missing) or shows dry-run report
        has_skip = "skip" in out.lower() or "Redis dashboard skipped" in out
        has_dry_run = "Dry run" in out or "Redis Dashboard" in out
        self.assertTrue(
            has_skip or has_dry_run,
            f"Expected skip or report output, got: {out!r}",
        )


if __name__ == "__main__":
    unittest.main()

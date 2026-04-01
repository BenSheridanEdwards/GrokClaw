"""Tests for the suggestion-to-linear draft approval workflow."""
import os
import subprocess
import unittest
from pathlib import Path


class ApprovalWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.approve_script = self.workspace / "tools" / "approve-suggestion.sh"
        self.smoke_script = self.workspace / "tools" / "approval-smoke.sh"

    def test_approve_suggestion_dry_run_exits_zero(self):
        """approve-suggestion.sh --dry-run exits 0 with valid args."""
        env = os.environ.copy()
        env["WORKSPACE_ROOT"] = str(self.workspace)
        result = subprocess.run(
            ["sh", str(self.approve_script), "--dry-run", "8", "Test title", "1234567890.123456", "Test desc"],
            env=env,
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

    def test_approve_suggestion_dry_run_prints_steps(self):
        """approve-suggestion.sh --dry-run prints draft request and inline approval steps."""
        env = os.environ.copy()
        env["WORKSPACE_ROOT"] = str(self.workspace)
        result = subprocess.run(
            ["sh", str(self.approve_script), "--dry-run", "8", "Test title", "1234567890.123456"],
            env=env,
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertEqual(result.returncode, 0)
        out = result.stdout + result.stderr
        self.assertIn("linear-draft-approval.sh request", out)
        self.assertIn("telegram-inline.sh", out)

    def test_approve_suggestion_fails_without_args(self):
        """approve-suggestion.sh exits 1 when given insufficient args."""
        env = os.environ.copy()
        env["WORKSPACE_ROOT"] = str(self.workspace)
        result = subprocess.run(
            ["sh", str(self.approve_script)],
            env=env,
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_approval_smoke_passes(self):
        """approval-smoke.sh exits 0 and validates the workflow."""
        env = os.environ.copy()
        env["WORKSPACE_ROOT"] = str(self.workspace)
        result = subprocess.run(
            ["sh", str(self.smoke_script)],
            env=env,
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("PASS", result.stdout + result.stderr)

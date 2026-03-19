"""Tests for superpowers workflow (GRO-27)."""
import subprocess
import unittest
from pathlib import Path


class SuperpowersTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.cursor_superpowers = self.workspace / "tools" / "cursor-superpowers.sh"
        self.skill_md = self.workspace / "skills" / "superpowers" / "SKILL.md"
        self.cursor_md = self.workspace / "CURSOR.md"

    def test_cursor_superpowers_script_exists_and_runs(self):
        """cursor-superpowers.sh exists, is executable, and exits 0."""
        self.assertTrue(self.cursor_superpowers.exists())
        self.assertTrue(self.cursor_superpowers.stat().st_mode & 0o111)
        result = subprocess.run(
            ["sh", str(self.cursor_superpowers)],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

    def test_cursor_superpowers_outputs_tdd_and_workflow(self):
        """cursor-superpowers.sh output includes TDD and workflow keywords."""
        result = subprocess.run(
            ["sh", str(self.cursor_superpowers)],
            capture_output=True,
            text=True,
            cwd=str(self.workspace),
        )
        self.assertEqual(result.returncode, 0)
        out = result.stdout.lower()
        self.assertIn("tdd", out, "Output should mention TDD")
        self.assertIn("brainstorm", out, "Output should mention brainstorm")
        self.assertIn("review", out, "Output should mention review")

    def test_skills_superpowers_skill_md_exists(self):
        """skills/superpowers/SKILL.md exists and describes workflow."""
        self.assertTrue(self.skill_md.exists())
        content = self.skill_md.read_text()
        self.assertIn("brainstorm", content.lower())
        self.assertIn("TDD", content)
        self.assertIn("obra/superpowers", content)

    def test_cursor_md_mandates_superpowers(self):
        """CURSOR.md mandates superpowers workflow."""
        content = self.cursor_md.read_text()
        self.assertIn("superpowers", content.lower())
        self.assertIn("TDD", content)
        self.assertIn("brainstorm", content.lower())

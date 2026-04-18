"""Tests for tools/_brief_validator.py — hallucination detection."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import _brief_validator as validator


class ExtractReposTests(unittest.TestCase):
    def test_pulls_bolded_owner_repo_mentions(self):
        md = "Some intro.\n**foo/bar** (100 stars) — desc\n**baz/qux-one** NEW\n"
        self.assertEqual(
            validator.extract_repo_mentions(md),
            {"foo/bar", "baz/qux-one"},
        )

    def test_ignores_file_path_slashes(self):
        md = "See `docs/prompts/cron-work-grok-daily-brief.md`.\n"
        self.assertEqual(validator.extract_repo_mentions(md), set())

    def test_ignores_url_slashes(self):
        md = "Visit https://github.com/foo/bar for details.\n"
        # Inline URLs are not bolded mentions; they should not count.
        self.assertEqual(validator.extract_repo_mentions(md), set())

    def test_captures_repo_listed_as_header(self):
        md = "### lost-pixel/lost-pixel\n\nNEW: ...\n"
        self.assertEqual(
            validator.extract_repo_mentions(md),
            {"lost-pixel/lost-pixel"},
        )


class ValidationTests(unittest.TestCase):
    def _write_discovery(self, ws: Path, date: str, repos):
        d = ws / "data" / "github-discover"
        d.mkdir(parents=True, exist_ok=True)
        starred, trending = [], []
        for name, src in repos:
            entry = {"name": name, "source": src, "stars": 1,
                     "description": "", "language": None,
                     "url": f"https://github.com/{name}"}
            (starred if src == "starred" else trending).append(entry)
        (d / f"{date}.json").write_text(json.dumps({
            "date": date, "starred": starred, "trending": trending,
        }))

    def _write_brief(self, ws: Path, date: str, body: str):
        b = ws / "data" / "briefs"
        b.mkdir(parents=True, exist_ok=True)
        (b / f"{date}.md").write_text(body)

    def test_no_hallucinations_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._write_discovery(ws, "2026-04-18", [
                ("foo/bar", "starred"), ("baz/qux", "trending"),
            ])
            self._write_brief(ws, "2026-04-18",
                              "**foo/bar** analysis\n**baz/qux** analysis\n")
            result = validator.validate_brief(str(ws), "2026-04-18")
            self.assertEqual(result.hallucinated, set())
            self.assertTrue(result.ok)

    def test_unknown_repo_is_hallucinated(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._write_discovery(ws, "2026-04-18", [("foo/bar", "starred")])
            self._write_brief(ws, "2026-04-18",
                              "**foo/bar** real\n**ghost/repo** fake\n")
            result = validator.validate_brief(str(ws), "2026-04-18")
            self.assertEqual(result.hallucinated, {"ghost/repo"})
            self.assertFalse(result.ok)

    def test_whitelisted_repo_is_not_hallucinated(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._write_discovery(ws, "2026-04-18", [("foo/bar", "starred")])
            self._write_brief(ws, "2026-04-18",
                              "Ben's repo **BenSheridanEdwards/GrokClaw** and "
                              "**foo/bar** analysis.\n")
            result = validator.validate_brief(
                str(ws), "2026-04-18",
                whitelist={"bensheridanedwards/grokclaw"},
            )
            self.assertEqual(result.hallucinated, set())
            self.assertTrue(result.ok)

    def test_missing_brief_returns_not_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._write_discovery(ws, "2026-04-18", [("foo/bar", "starred")])
            result = validator.validate_brief(str(ws), "2026-04-18")
            self.assertFalse(result.ok)
            self.assertIn("brief_missing", result.errors)

    def test_missing_discovery_returns_not_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._write_brief(ws, "2026-04-18", "**foo/bar** analysis\n")
            result = validator.validate_brief(str(ws), "2026-04-18")
            self.assertFalse(result.ok)
            self.assertIn("discovery_missing", result.errors)


class CliTests(unittest.TestCase):
    def test_cli_exits_nonzero_on_hallucination(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "data" / "github-discover").mkdir(parents=True)
            (ws / "data" / "github-discover" / "2026-04-18.json").write_text(
                json.dumps({"date": "2026-04-18",
                            "starred": [{"name": "foo/bar", "source": "starred"}],
                            "trending": []})
            )
            (ws / "data" / "briefs").mkdir(parents=True)
            (ws / "data" / "briefs" / "2026-04-18.md").write_text(
                "**ghost/repo** hallucinated\n"
            )
            rc = validator.main([
                "_brief_validator.py", "--workspace", str(ws), "--date", "2026-04-18",
            ])
            self.assertNotEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()

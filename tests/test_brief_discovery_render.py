"""Tests for tools/_brief_discovery_render.py."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import _brief_discovery_render as render


class LoadDiscoveryTests(unittest.TestCase):
    def test_returns_starred_and_trending_from_todays_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            disc = ws / "data" / "github-discover"
            disc.mkdir(parents=True)
            (disc / "2026-04-18.json").write_text(json.dumps({
                "date": "2026-04-18",
                "starred": [{"name": "foo/bar", "stars": 10, "description": "d",
                             "language": "Python", "source": "starred", "url": "u"}],
                "trending": [{"name": "baz/qux", "stars": 100, "description": "d2",
                              "language": "TypeScript", "source": "trending", "url": "u2"}],
            }))
            data = render.load_discovery(str(ws), "2026-04-18")
            self.assertEqual(len(data["starred"]), 1)
            self.assertEqual(data["starred"][0]["name"], "foo/bar")
            self.assertEqual(data["trending"][0]["name"], "baz/qux")

    def test_missing_file_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(render.load_discovery(tmp, "2099-01-01"))


class StackIndexTests(unittest.TestCase):
    def _seed_workspace(self, tmp):
        ws = Path(tmp)
        (ws / "memory").mkdir()
        (ws / "docs" / "prompts").mkdir(parents=True)
        (ws / "graphify-out" / "wiki").mkdir(parents=True)
        (ws / "memory" / "MEMORY.md").write_text(
            "Uses karpathy/autoresearch for structured market research.\n"
        )
        (ws / "NorthStar.md").write_text("Integrates MemPalace for agent memory.\n")
        (ws / "AGENTS.md").write_text("\n")
        (ws / "README.md").write_text("\n")
        (ws / "docs" / "prompts" / "cron-work-alpha-polymarket.md").write_text(
            "calls autoresearch in the deterministic phase.\n"
        )
        (ws / "graphify-out" / "wiki" / "index.md").write_text(
            "graphify builds the knowledge graph.\n"
        )
        return ws

    def test_index_contains_explicit_owner_repo_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = self._seed_workspace(tmp)
            idx = render.load_stack_index(str(ws))
            self.assertIn("karpathy/autoresearch", idx["slugs"])

    def test_index_contains_bare_names_mentioned_in_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = self._seed_workspace(tmp)
            idx = render.load_stack_index(str(ws))
            self.assertIn("mempalace", idx["names"])
            self.assertIn("autoresearch", idx["names"])
            self.assertIn("graphify", idx["names"])


class ClassifyRepoTests(unittest.TestCase):
    def test_slug_match_is_in_stack(self):
        idx = {"slugs": {"karpathy/autoresearch"}, "names": set()}
        repo = {"name": "karpathy/autoresearch", "description": ""}
        self.assertEqual(render.classify_repo(repo, idx), "IN_STACK")

    def test_bare_name_match_is_in_stack(self):
        idx = {"slugs": set(), "names": {"mempalace"}}
        repo = {"name": "MemPalace/mempalace", "description": "memory system"}
        self.assertEqual(render.classify_repo(repo, idx), "IN_STACK")

    def test_no_match_is_new(self):
        idx = {"slugs": set(), "names": {"mempalace"}}
        repo = {"name": "lost-pixel/lost-pixel", "description": "visual regression"}
        self.assertEqual(render.classify_repo(repo, idx), "NEW")

    def test_common_word_in_repo_name_does_not_false_match(self):
        # A stack index with common name "test" shouldn't mark every repo with
        # "test" in its slug as in-stack.
        idx = {"slugs": set(), "names": {"test"}}
        repo = {"name": "someorg/testutil", "description": ""}
        self.assertEqual(render.classify_repo(repo, idx), "NEW")


class RecentlySurfacedTests(unittest.TestCase):
    def test_repo_mentioned_in_prior_brief_is_recent(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            briefs = ws / "data" / "briefs"
            briefs.mkdir(parents=True)
            (briefs / "2026-04-17.md").write_text("**lost-pixel/lost-pixel** (1k stars)\n")
            self.assertTrue(render.recently_surfaced(
                "lost-pixel/lost-pixel", str(ws), today="2026-04-18", days=7,
            ))

    def test_repo_not_in_recent_briefs_is_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "data" / "briefs").mkdir(parents=True)
            self.assertFalse(render.recently_surfaced(
                "new/thing", str(ws), today="2026-04-18", days=7,
            ))

    def test_mention_outside_window_is_not_recent(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            briefs = ws / "data" / "briefs"
            briefs.mkdir(parents=True)
            (briefs / "2026-03-01.md").write_text("**old/repo** mentioned\n")
            self.assertFalse(render.recently_surfaced(
                "old/repo", str(ws), today="2026-04-18", days=7,
            ))


class RenderBlockTests(unittest.TestCase):
    def _seed(self, ws: Path, disc_json: dict):
        (ws / "memory").mkdir()
        (ws / "memory" / "MEMORY.md").write_text("Uses graphify for knowledge graphs.\n")
        (ws / "NorthStar.md").write_text("\n")
        (ws / "AGENTS.md").write_text("\n")
        (ws / "README.md").write_text("\n")
        (ws / "docs" / "prompts").mkdir(parents=True)
        (ws / "docs" / "prompts" / "cron-work-alpha-polymarket.md").write_text("\n")
        (ws / "graphify-out" / "wiki").mkdir(parents=True)
        (ws / "graphify-out" / "wiki" / "index.md").write_text("\n")
        (ws / "data" / "briefs").mkdir(parents=True)
        disc = ws / "data" / "github-discover"
        disc.mkdir(parents=True)
        (disc / "2026-04-18.json").write_text(json.dumps(disc_json))

    def test_block_lists_every_repo_from_json_with_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._seed(ws, {
                "date": "2026-04-18",
                "starred": [
                    {"name": "multica-ai/multica", "stars": 15691,
                     "language": "TypeScript",
                     "description": "Managed agents platform.",
                     "source": "starred", "url": "u"},
                    {"name": "safishamsi/graphify", "stars": 24156,
                     "language": "Python",
                     "description": "Knowledge graph skill.",
                     "source": "starred", "url": "u"},
                ],
                "trending": [
                    {"name": "AgentSeal/codeburn", "stars": 2624,
                     "language": "TypeScript",
                     "description": "TUI token dashboard.",
                     "source": "trending", "url": "u"},
                ],
            })
            block = render.render_block(str(ws), "2026-04-18")
            self.assertIn("multica-ai/multica", block)
            self.assertIn("15691", block)
            self.assertIn("Managed agents platform.", block)
            # graphify is in MEMORY.md so it should be labeled IN_STACK
            self.assertRegex(block, r"safishamsi/graphify.*IN[_ ]STACK")
            # multica is not referenced anywhere, so NEW
            self.assertRegex(block, r"multica-ai/multica.*NEW")
            # trending repo appears
            self.assertIn("AgentSeal/codeburn", block)

    def test_block_reports_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "memory").mkdir()
            (ws / "memory" / "MEMORY.md").write_text("\n")
            (ws / "NorthStar.md").write_text("\n")
            (ws / "AGENTS.md").write_text("\n")
            (ws / "README.md").write_text("\n")
            block = render.render_block(str(ws), "2099-01-01")
            self.assertIn("Discovery file not found", block)

    def test_block_marks_recently_surfaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._seed(ws, {
                "date": "2026-04-18",
                "starred": [
                    {"name": "foo/bar", "stars": 100,
                     "language": "Python", "description": "Something new.",
                     "source": "starred", "url": "u"},
                ],
                "trending": [],
            })
            (ws / "data" / "briefs" / "2026-04-17.md").write_text(
                "**foo/bar** was discussed yesterday.\n"
            )
            block = render.render_block(str(ws), "2026-04-18")
            self.assertIn("foo/bar", block)
            self.assertIn("SEEN_RECENTLY", block)


if __name__ == "__main__":
    unittest.main()

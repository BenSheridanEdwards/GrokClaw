"""Tests for tools/_linear_workflow_health_cleanup.py."""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch
import io
from contextlib import redirect_stdout

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import _linear_workflow_health_cleanup as lwh  # noqa: E402


class LinearWorkflowHealthCleanupTests(unittest.TestCase):
    def test_cleanup_title_matches_workflow_health_draft(self) -> None:
        import importlib.util

        path = ROOT / "tools" / "_workflow_health.py"
        spec = importlib.util.spec_from_file_location("workflow_health_mod", path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        draft = mod.build_draft([], "deadbeef")
        self.assertEqual(draft["title"], lwh.WORKFLOW_HEALTH_ISSUE_TITLE)

    def test_find_open_filters_exact_title_and_terminal(self) -> None:
        sample = {
            "data": {
                "issues": {
                    "nodes": [
                        {
                            "id": "a",
                            "identifier": "GRO-1",
                            "title": lwh.WORKFLOW_HEALTH_ISSUE_TITLE,
                            "state": {"name": "Todo"},
                        },
                        {
                            "id": "b",
                            "identifier": "GRO-2",
                            "title": lwh.WORKFLOW_HEALTH_ISSUE_TITLE + " extra",
                            "state": {"name": "Todo"},
                        },
                        {
                            "id": "c",
                            "identifier": "GRO-3",
                            "title": lwh.WORKFLOW_HEALTH_ISSUE_TITLE,
                            "state": {"name": "Done"},
                        },
                    ]
                }
            }
        }

        with patch.dict(os.environ, {"LINEAR_TEAM_ID": "team-test-id"}, clear=False):
            with patch.object(lwh, "graphql", return_value=sample):
                open_issues = lwh.find_open_workflow_health_issues("fake-key")
        ids = {n["id"] for n in open_issues}
        self.assertEqual(ids, {"a"})

    def test_graphql_error_raises(self) -> None:
        with patch.dict(os.environ, {"LINEAR_TEAM_ID": "team-test-id"}, clear=False):
            with patch.object(
                lwh, "graphql", return_value={"errors": [{"message": "bad"}]}
            ):
                with self.assertRaises(RuntimeError):
                    lwh.find_open_workflow_health_issues("k")

    def test_cancel_issue_parses_success(self) -> None:
        payload = {
            "data": {
                "issueUpdate": {
                    "success": True,
                    "issue": {"identifier": "GRO-9", "state": {"name": "Canceled"}},
                }
            }
        }
        with patch.object(lwh, "graphql", return_value=payload):
            res = lwh.cancel_issue("k", "internal-id")
        self.assertTrue(res.get("success"))

    def test_plan_removes_draft_files(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "data"
            d.mkdir()
            f = d / "pending-linear-draft-workflow-health-abc.json"
            f.write_text("{}", encoding="utf-8")
            sf = root / ".openclaw" / "state"
            sf.mkdir(parents=True)
            st = sf / "workflow-health-failures.json"
            st.write_text('{"status":"open"}\n', encoding="utf-8")

            with patch.object(lwh, "state_file", return_value=st):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = lwh.plan_and_apply(
                        api_key=None,
                        root=root,
                        apply=True,
                        skip_linear=True,
                        skip_drafts=False,
                        skip_state=False,
                    )
            self.assertEqual(rc, 0)
            self.assertFalse(f.exists())
            data = json.loads(st.read_text(encoding="utf-8"))
            self.assertEqual(data.get("status"), "resolved")


if __name__ == "__main__":
    unittest.main()

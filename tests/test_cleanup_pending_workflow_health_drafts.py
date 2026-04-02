import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class CleanupPendingWorkflowHealthDraftsTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.script = self.repo_root / "tools" / "cleanup-pending-workflow-health-drafts.sh"

    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_dry_run_reports_but_does_not_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            data_dir = workspace / "data"

            old = data_dir / "pending-linear-draft-workflow-health-old.json"
            new = data_dir / "pending-linear-draft-workflow-health-new.json"
            created = data_dir / "pending-linear-draft-workflow-health-created.json"

            self._write_json(
                old,
                {
                    "flow": "suggestion",
                    "referenceId": "dup-old",
                    "title": "Fix workflow health failure in core cron workflows",
                },
            )
            self._write_json(
                new,
                {
                    "flow": "suggestion",
                    "referenceId": "dup-new",
                    "title": "Fix workflow health failure in core cron workflows",
                },
            )
            self._write_json(
                created,
                {
                    "flow": "suggestion",
                    "referenceId": "created-ref",
                    "title": "Fix workflow health failure in core cron workflows",
                },
            )

            os.utime(old, (1000, 1000))
            os.utime(new, (2000, 2000))
            os.utime(created, (3000, 3000))

            linear_log = data_dir / "linear-creations" / "2026-04-02.jsonl"
            linear_log.parent.mkdir(parents=True, exist_ok=True)
            linear_log.write_text(
                json.dumps(
                    {
                        "ts": "2026-04-02T05:33:44Z",
                        "flow": "suggestion",
                        "referenceId": "created-ref",
                        "title": "Fix workflow health failure in core cron workflows",
                        "url": "https://linear.app/grokclaw/issue/GRO-43/fix-workflow-health-failure-in-core-cron-workflows",
                        "agent": "grok",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                ["sh", str(self.script)],
                cwd=str(self.repo_root),
                env={**os.environ, "WORKSPACE_ROOT": str(workspace)},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("dry-run", result.stdout)
            self.assertIn("superseded_by_newer_draft", result.stdout)
            self.assertIn("linear_ticket_already_created", result.stdout)
            self.assertTrue(old.exists())
            self.assertTrue(new.exists())
            self.assertTrue(created.exists())

    def test_apply_deletes_stale_and_keeps_latest_uncreated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            data_dir = workspace / "data"

            old = data_dir / "pending-linear-draft-workflow-health-old.json"
            latest = data_dir / "pending-linear-draft-workflow-health-latest.json"
            unique = data_dir / "pending-linear-draft-workflow-health-unique.json"

            self._write_json(
                old,
                {
                    "flow": "suggestion",
                    "referenceId": "dup-old",
                    "title": "Fix workflow health failure in core cron workflows",
                },
            )
            self._write_json(
                latest,
                {
                    "flow": "suggestion",
                    "referenceId": "dup-latest",
                    "title": "Fix workflow health failure in core cron workflows",
                },
            )
            self._write_json(
                unique,
                {
                    "flow": "suggestion",
                    "referenceId": "unique-ref",
                    "title": "Fix another workflow health class",
                },
            )

            os.utime(old, (1000, 1000))
            os.utime(latest, (2000, 2000))
            os.utime(unique, (1500, 1500))

            result = subprocess.run(
                ["sh", str(self.script), "--apply"],
                cwd=str(self.repo_root),
                env={**os.environ, "WORKSPACE_ROOT": str(workspace)},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("Deleted 1 stale draft file(s)", result.stdout)
            self.assertFalse(old.exists())
            self.assertTrue(latest.exists())
            self.assertTrue(unique.exists())


if __name__ == "__main__":
    unittest.main()

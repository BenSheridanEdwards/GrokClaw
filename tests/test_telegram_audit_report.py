import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class TelegramAuditReportTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "telegram-audit-report.sh"

    def test_report_summarizes_inbound_outbound_and_flags(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            audit_dir = workspace / "data" / "audit-log"
            audit_dir.mkdir(parents=True, exist_ok=True)
            (audit_dir / "2026-04-02.jsonl").write_text(
                "\n".join(
                    [
                        '{"ts":"2026-04-02T08:00:00Z","kind":"telegram_post","topic":"suggestions","topicId":"2","message":"ok"}',
                        '{"ts":"2026-04-02T08:01:00Z","kind":"telegram_inline","topic":"suggestions","topicId":"2","message":"Daily Suggestion #12 Improve deployment validation"}',
                        '{"ts":"2026-04-02T08:02:00Z","kind":"telegram_post_failed","topic":"health","topicId":"4","message":"Gateway down after restart"}',
                        '{"ts":"2026-04-02T08:03:00Z","kind":"telegram_incoming","topic":"actions","topicId":"approve_suggestion:12","message":"Approve | approve_suggestion:12"}',
                        '{"ts":"2026-04-02T08:04:00Z","kind":"telegram_incoming","topic":"actions","topicId":"approve-now","message":"Approve now"}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                ["sh", str(self.script), "--date", "2026-04-02", "--days", "1"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("Total events: 5", result.stdout)
            self.assertIn("Inbound actions: 2", result.stdout)
            self.assertIn("Outbound sent: 2", result.stdout)
            self.assertIn("Outbound failed: 1", result.stdout)
            self.assertIn("too_short", result.stdout)
            self.assertIn("invalid_action_token", result.stdout)
            self.assertIn("bad_message=ok", result.stdout)
            self.assertIn("improve_to=", result.stdout)
            self.assertIn("Approve | approve_suggestion:12", result.stdout)

    def test_report_respects_date_window(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            audit_dir = workspace / "data" / "audit-log"
            audit_dir.mkdir(parents=True, exist_ok=True)
            (audit_dir / "2026-04-01.jsonl").write_text(
                '{"ts":"2026-04-01T08:00:00Z","kind":"telegram_post","topic":"health","topicId":"4","message":"Yesterday"}\n',
                encoding="utf-8",
            )
            (audit_dir / "2026-04-02.jsonl").write_text(
                '{"ts":"2026-04-02T08:00:00Z","kind":"telegram_post","topic":"health","topicId":"4","message":"Today"}\n',
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                ["sh", str(self.script), "--date", "2026-04-02", "--days", "1"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("Total events: 1", result.stdout)
            self.assertIn("Today", result.stdout)
            self.assertNotIn("Yesterday", result.stdout)


if __name__ == "__main__":
    unittest.main()

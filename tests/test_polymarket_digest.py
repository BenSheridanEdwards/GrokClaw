import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tools import _polymarket_digest as digest


class PolymarketDigestTests(unittest.TestCase):
    def test_digest_payload_is_single_json_line(self):
        payload = digest.build_payload("Line one\nLine two", "Review worst call")

        self.assertTrue(payload.startswith("DIGEST_JSON:"))
        parsed = json.loads(payload.removeprefix("DIGEST_JSON:"))
        self.assertEqual(parsed["slack_msg"], "Line one\nLine two")
        self.assertEqual(parsed["improvement"], "Review worst call")

    def test_recent_results_use_resolution_date_not_trade_date(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "results.jsonl"
            entries = [
                {
                    "date": "2026-03-01",
                    "resolved_at": "2026-03-14",
                    "question": "Recent resolution",
                    "won": True,
                    "pnl": 1.0,
                },
                {
                    "date": "2026-03-14",
                    "resolved_at": "2026-03-01",
                    "question": "Old resolution",
                    "won": False,
                    "pnl": -1.0,
                },
            ]
            with results_path.open("w", encoding="utf-8") as handle:
                for entry in entries:
                    handle.write(json.dumps(entry) + "\n")

            now = datetime(2026, 3, 14, tzinfo=timezone.utc)
            results = digest.load_recent_results(results_path, now)

            self.assertEqual([result["question"] for result in results], ["Recent resolution"])

    def test_digest_state_prevents_duplicate_weekly_emission(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            now = datetime(2026, 3, 16, tzinfo=timezone.utc)

            self.assertFalse(digest.digest_already_recorded(workspace, now))
            digest.mark_digest_recorded(workspace, now)
            self.assertTrue(digest.digest_already_recorded(workspace, now))
            self.assertFalse(digest.digest_already_recorded(workspace, datetime(2026, 3, 23, tzinfo=timezone.utc)))


if __name__ == "__main__":
    unittest.main()

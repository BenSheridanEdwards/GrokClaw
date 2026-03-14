import json
import math
import tempfile
import unittest
from pathlib import Path

from tools import _polymarket_metrics as metrics
from tools import _polymarket_trade as trade


class PolymarketTradeTests(unittest.TestCase):
    def test_validate_odds_rejects_non_finite_or_out_of_range_values(self):
        for bad_value in ("0", "-0.1", "1.5", "nan", "abc"):
            with self.assertRaises(ValueError):
                trade.validate_odds(bad_value)

        self.assertTrue(math.isclose(trade.validate_odds("0.72"), 0.72))

    def test_stage_then_record_trade_uses_pending_candidate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            candidate = {
                "date": "2026-03-14",
                "market_id": "123",
                "question": "Will X happen?",
                "odds_yes": 0.72,
                "odds_no": 0.28,
            }

            trade.stage_candidate(workspace, candidate)
            trade.log_staged_trade(workspace, "YES", "high conviction")

            trades_path = workspace / "data" / "polymarket-trades.json"
            pending_path = workspace / "data" / "polymarket-pending-trade.json"

            with trades_path.open(encoding="utf-8") as handle:
                entries = [json.loads(line) for line in handle if line.strip()]

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["market_id"], "123")
            self.assertEqual(entries[0]["side"], "YES")
            self.assertEqual(entries[0]["odds"], 0.72)
            self.assertFalse(pending_path.exists())

    def test_fetch_mode_uses_explicit_workspace_argument(self):
        self.assertEqual(
            trade.resolve_workspace_root(["prog", "/tmp/custom-workspace"]),
            "/tmp/custom-workspace",
        )

    def test_already_decided_today_detects_prior_skip_or_trade(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            metrics.append_jsonl(
                workspace / "data" / "polymarket-decisions.json",
                {"date": "2026-03-14", "action": "skip"},
            )

            original_datetime = trade.datetime
            class FixedDateTime:
                @staticmethod
                def now(_tz):
                    return original_datetime(2026, 3, 14, tzinfo=_tz)
            trade.datetime = FixedDateTime
            try:
                self.assertTrue(trade.already_decided_today(workspace))
            finally:
                trade.datetime = original_datetime


if __name__ == "__main__":
    unittest.main()

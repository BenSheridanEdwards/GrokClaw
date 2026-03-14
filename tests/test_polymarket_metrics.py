import json
import tempfile
import unittest
from pathlib import Path

from tools import _polymarket_metrics as metrics


class PolymarketMetricsTests(unittest.TestCase):
    def test_current_bankroll_defaults_to_starting_balance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertEqual(metrics.current_bankroll(tmpdir), 1000.0)

    def test_record_bankroll_event_appends_running_balance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            entry = metrics.record_bankroll_event(
                tmpdir,
                {
                    "date": "2026-03-14",
                    "kind": "resolved_trade",
                    "market_id": "m1",
                    "delta": 125.5,
                },
            )

            ledger_path = Path(tmpdir) / "data" / "polymarket-bankroll.json"
            with ledger_path.open(encoding="utf-8") as handle:
                rows = [json.loads(line) for line in handle if line.strip()]

            self.assertEqual(entry["bankroll_before"], 1000.0)
            self.assertEqual(entry["bankroll_after"], 1125.5)
            self.assertEqual(rows[-1]["bankroll_after"], 1125.5)

    def test_promotion_gate_requires_more_than_bankroll_target(self):
        summary = {
            "current_bankroll": 100500.0,
            "resolved_count": 50,
            "last100_expectancy": 1.2,
            "max_drawdown": 0.05,
            "brier_score": 0.08,
        }

        result = metrics.check_promotion_gate(summary)

        self.assertFalse(result["eligible"])
        self.assertIn("resolved_count", result["blocked_on"])


if __name__ == "__main__":
    unittest.main()

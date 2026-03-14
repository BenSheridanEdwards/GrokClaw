import json
import tempfile
import unittest
from datetime import datetime, timezone
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

    def test_summarize_scopes_drawdown_to_requested_window(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bankroll_path = Path(tmpdir) / "data" / "polymarket-bankroll.json"
            bankroll_path.parent.mkdir(parents=True, exist_ok=True)
            rows = [
                {"date": "2026-03-01", "bankroll_after": 700.0},
                {"date": "2026-03-10", "bankroll_after": 900.0},
                {"date": "2026-03-14", "bankroll_after": 1100.0},
            ]
            with bankroll_path.open("w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row) + "\n")

            summary = metrics.summarize(
                tmpdir,
                days=7,
                now=datetime(2026, 3, 14, tzinfo=timezone.utc),
            )

            self.assertEqual(summary["max_drawdown"], 0.0)

    def test_promotion_alert_only_fires_on_transition(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertTrue(metrics.should_send_promotion_alert(tmpdir, True))
            metrics.mark_promotion_alert_state(tmpdir, True)
            self.assertFalse(metrics.should_send_promotion_alert(tmpdir, True))
            metrics.mark_promotion_alert_state(tmpdir, False)
            self.assertTrue(metrics.should_send_promotion_alert(tmpdir, True))


if __name__ == "__main__":
    unittest.main()

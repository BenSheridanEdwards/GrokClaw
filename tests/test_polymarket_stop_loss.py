"""Tests for tools/_polymarket_stop_loss.py.

Voids open trades where the current market price has moved 30pp or more
against the entry side. The goal: treat paper-money trades the way a real
trader would — when you're clearly wrong, close for a known loss instead
of hoping for reversal. Frees bankroll for better signals.
"""
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools import _polymarket_stop_loss as stop


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def read_jsonl(path: Path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


class StopLossTests(unittest.TestCase):
    def test_voids_yes_trade_when_price_drops_past_threshold(self):
        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            trade = {
                "date": "2026-04-18",
                "market_id": "m-1",
                "question": "Will thing happen by Friday?",
                "side": "YES",
                "odds": 0.60,
                "stake_amount": 20.0,
                "resolved": False,
            }
            write_jsonl(workspace / "data" / "polymarket-trades.json", [trade])

            def fake_fetch(market_id):
                return {"outcomePrices": ["0.25", "0.75"]}

            summary = stop.run_stop_loss(
                str(workspace), drop_threshold=0.30, fetch_market=fake_fetch,
            )
            self.assertEqual(summary["voided"], 1)
            trades = read_jsonl(workspace / "data" / "polymarket-trades.json")
            self.assertTrue(trades[0]["voided"])
            self.assertTrue(trades[0]["resolved"])

    def test_voids_no_trade_when_price_rises_past_threshold(self):
        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            trade = {
                "date": "2026-04-18",
                "market_id": "m-2",
                "question": "Will thing happen?",
                "side": "NO",
                "odds": 0.70,
                "stake_amount": 15.0,
                "resolved": False,
            }
            write_jsonl(workspace / "data" / "polymarket-trades.json", [trade])

            def fake_fetch(market_id):
                return {"outcomePrices": ["0.65", "0.35"]}

            summary = stop.run_stop_loss(
                str(workspace), drop_threshold=0.30, fetch_market=fake_fetch,
            )
            self.assertEqual(summary["voided"], 1)

    def test_does_not_void_when_price_holds(self):
        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            trade = {
                "date": "2026-04-18",
                "market_id": "m-3",
                "question": "Will thing happen?",
                "side": "YES",
                "odds": 0.60,
                "stake_amount": 20.0,
                "resolved": False,
            }
            write_jsonl(workspace / "data" / "polymarket-trades.json", [trade])

            def fake_fetch(market_id):
                return {"outcomePrices": ["0.55", "0.45"]}

            summary = stop.run_stop_loss(
                str(workspace), drop_threshold=0.30, fetch_market=fake_fetch,
            )
            self.assertEqual(summary["voided"], 0)

    def test_records_realized_loss_delta_not_full_stake(self):
        """A stop-loss voids at current price — real loss is (entry - exit) * stake, not the whole stake."""
        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            trade = {
                "date": "2026-04-18",
                "market_id": "m-4",
                "question": "Will thing happen?",
                "side": "YES",
                "odds": 0.60,
                "stake_amount": 20.0,
                "resolved": False,
            }
            write_jsonl(workspace / "data" / "polymarket-trades.json", [trade])

            def fake_fetch(market_id):
                return {"outcomePrices": ["0.20", "0.80"]}  # YES side lost 40pp

            summary = stop.run_stop_loss(
                str(workspace), drop_threshold=0.30, fetch_market=fake_fetch,
            )
            self.assertEqual(summary["voided"], 1)
            bankroll = read_jsonl(workspace / "data" / "polymarket-bankroll.json")
            # Entry 0.60 → exit 0.20; realized = stake * (exit - entry) / entry = 20 * (-0.40/0.60)
            expected_delta = round(20.0 * (0.20 - 0.60) / 0.60, 2)
            self.assertAlmostEqual(bankroll[-1]["delta"], expected_delta, places=2)
            self.assertEqual(bankroll[-1]["kind"], "stop_loss")


if __name__ == "__main__":
    unittest.main()

"""Tests for tools/_polymarket_stale_voider.py — void trades past endDate+N.

The problem this fixes: paper-money trades whose market is still `closed: false`
on Polymarket's side days after their stated endDate sit in open_exposure
forever and block new trades via the exposure cap. Grace-period resolution
covers the "price collapsed" case, but leaves trades with indeterminate prices
(still hovering 0.3-0.7) stuck indefinitely. This tool voids those — returns
the stake to bankroll, marks the trade resolved+voided, and logs the event.
"""
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools import _polymarket_stale_voider as voider


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


class StaleVoiderTests(unittest.TestCase):
    def test_voids_trade_past_cutoff_returns_stake_to_bankroll(self):
        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            stale_end = (datetime.now(timezone.utc) - timedelta(days=5)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            trade = {
                "date": "2026-04-10",
                "market_id": "m-stale",
                "question": "Stale Iran question resolved in real life?",
                "side": "YES",
                "odds": 0.4,
                "stake_amount": 20.0,
                "endDate": stale_end,
                "resolved": False,
            }
            write_jsonl(workspace / "data" / "polymarket-trades.json", [trade])
            write_jsonl(
                workspace / "data" / "polymarket-bankroll.json",
                [
                    {
                        "date": "2026-04-10",
                        "kind": "trade_open",
                        "market_id": "m-stale",
                        "question": trade["question"],
                        "delta": -20.0,
                        "bankroll_before": 1000.0,
                        "bankroll_after": 980.0,
                    }
                ],
            )

            summary = voider.void_stale_trades(str(workspace), stale_hours=48)

            self.assertEqual(summary["voided"], 1)
            self.assertEqual(summary["voided_market_ids"], ["m-stale"])

            trades = read_jsonl(workspace / "data" / "polymarket-trades.json")
            self.assertTrue(trades[0]["resolved"])
            self.assertTrue(trades[0].get("voided"))

            bankroll = read_jsonl(workspace / "data" / "polymarket-bankroll.json")
            self.assertEqual(bankroll[-1]["kind"], "voided_stale_trade")
            self.assertAlmostEqual(bankroll[-1]["delta"], 20.0, places=2)
            self.assertAlmostEqual(bankroll[-1]["bankroll_after"], 1000.0, places=2)

    def test_leaves_fresh_trade_untouched(self):
        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            fresh_end = (datetime.now(timezone.utc) + timedelta(days=2)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            trade = {
                "date": "2026-04-17",
                "market_id": "m-fresh",
                "question": "Future BTC question",
                "side": "YES",
                "odds": 0.5,
                "stake_amount": 15.0,
                "endDate": fresh_end,
                "resolved": False,
            }
            write_jsonl(workspace / "data" / "polymarket-trades.json", [trade])

            summary = voider.void_stale_trades(str(workspace), stale_hours=48)

            self.assertEqual(summary["voided"], 0)
            trades = read_jsonl(workspace / "data" / "polymarket-trades.json")
            self.assertFalse(trades[0]["resolved"])

    def test_leaves_already_resolved_trade_untouched(self):
        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            stale_end = (datetime.now(timezone.utc) - timedelta(days=10)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            trade = {
                "date": "2026-04-01",
                "market_id": "m-done",
                "question": "Already resolved Iran deal?",
                "side": "YES",
                "odds": 0.3,
                "stake_amount": 10.0,
                "endDate": stale_end,
                "resolved": True,
                "resolved_at": "2026-04-02",
            }
            write_jsonl(workspace / "data" / "polymarket-trades.json", [trade])

            summary = voider.void_stale_trades(str(workspace), stale_hours=48)
            self.assertEqual(summary["voided"], 0)

    def test_missing_enddate_is_voided_if_trade_older_than_cutoff(self):
        """Some legacy trades have no endDate — fall back to trade date + stale_hours."""
        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            trade = {
                "date": "2026-04-01",
                "market_id": "m-noend",
                "question": "Legacy trade with no endDate",
                "side": "YES",
                "odds": 0.5,
                "stake_amount": 5.0,
                "resolved": False,
            }
            write_jsonl(workspace / "data" / "polymarket-trades.json", [trade])

            summary = voider.void_stale_trades(str(workspace), stale_hours=48)
            self.assertEqual(summary["voided"], 1)


if __name__ == "__main__":
    unittest.main()

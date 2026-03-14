import json
import tempfile
import unittest
from pathlib import Path

from tools import _polymarket_decide as decide
from tools import _polymarket_trade as trade


class PolymarketDecideTests(unittest.TestCase):
    def stage_candidate(self, workspace):
        trade.stage_candidate(
            workspace,
            {
                "date": "2026-03-14",
                "market_id": "123",
                "question": "Will X happen?",
                "odds_yes": 0.52,
                "odds_no": 0.48,
                "volume": 50000,
                "endDate": "2026-03-20T00:00:00Z",
            },
        )

    def test_trade_decision_records_trade_when_gates_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self.stage_candidate(workspace)

            decision = decide.evaluate_staged_candidate(
                workspace,
                "YES",
                0.65,
                0.8,
                "The market is underpricing the likely outcome.",
            )

            self.assertEqual(decision["action"], "trade")
            self.assertLessEqual(decision["stake_fraction"], 0.02)

            trades_path = workspace / "data" / "polymarket-trades.json"
            with trades_path.open(encoding="utf-8") as handle:
                trades = [json.loads(line) for line in handle if line.strip()]
            self.assertEqual(len(trades), 1)

    def test_trade_decision_records_skip_when_edge_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self.stage_candidate(workspace)

            decision = decide.evaluate_staged_candidate(
                workspace,
                "YES",
                0.54,
                0.8,
                "Tiny edge is not enough to justify a trade.",
            )

            self.assertEqual(decision["action"], "skip")
            self.assertIn("edge_below_threshold", decision["gate_failures"])

            skips_path = workspace / "data" / "polymarket-skips.json"
            with skips_path.open(encoding="utf-8") as handle:
                skips = [json.loads(line) for line in handle if line.strip()]
            self.assertEqual(len(skips), 1)

    def test_explicit_skip_records_reason_and_clears_candidate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self.stage_candidate(workspace)

            decision = decide.record_explicit_skip(
                workspace,
                "Insufficient confidence after research.",
            )

            self.assertEqual(decision["action"], "skip")
            self.assertFalse((workspace / "data" / "polymarket-pending-trade.json").exists())


if __name__ == "__main__":
    unittest.main()

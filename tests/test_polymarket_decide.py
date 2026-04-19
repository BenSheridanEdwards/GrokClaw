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

    def stage_candidate_bonding(self, workspace):
        trade.stage_candidate(
            workspace,
            {
                "date": "2026-03-14",
                "market_id": "456",
                "question": "Will X resolve YES by tonight?",
                "odds_yes": 0.98,
                "odds_no": 0.02,
                "volume": 12000,
                "endDate": "2026-03-14T22:00:00Z",
                "selection_source": "bonding_copy",
                "copy_strategy": {
                    "consensus_probability_yes": 0.985,
                    "confidence": 0.8,
                    "traders_with_matching_positions": 2,
                },
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

    def test_topic_concentration_cap_blocks_fourth_open_cluster_trade(self):
        """Stop news-cycle concentration: 3 open trades in a cluster caps the 4th."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            trades_dir = workspace / "data"
            trades_dir.mkdir(parents=True, exist_ok=True)
            trades_path = trades_dir / "polymarket-trades.json"
            existing = [
                {"market_id": "t1", "question": "Iran nuclear deal by April 30?",
                 "side": "YES", "odds": 0.1, "stake_amount": 10},
                {"market_id": "t2", "question": "US escorts through Hormuz?",
                 "side": "YES", "odds": 0.1, "stake_amount": 10},
                {"market_id": "t3", "question": "Iran uranium surrender?",
                 "side": "YES", "odds": 0.1, "stake_amount": 10},
            ]
            with trades_path.open("w", encoding="utf-8") as fh:
                for t in existing:
                    fh.write(json.dumps(t) + "\n")

            trade.stage_candidate(
                workspace,
                {
                    "date": "2026-04-18",
                    "market_id": "t4",
                    "question": "US x Iran diplomatic breakthrough by May 1?",
                    "odds_yes": 0.30,
                    "odds_no": 0.70,
                    "volume": 50000,
                    "endDate": "2026-05-01T00:00:00Z",
                },
            )

            decision = decide.evaluate_staged_candidate(
                workspace, "YES", 0.85, 0.9,
                "Four matching whales say YES, but cluster is saturated.",
            )

            self.assertEqual(decision["action"], "skip")
            self.assertIn("topic_concentration_cap", decision["gate_failures"])

    def test_topic_concentration_cap_does_not_block_different_cluster(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            trades_dir = workspace / "data"
            trades_dir.mkdir(parents=True, exist_ok=True)
            trades_path = trades_dir / "polymarket-trades.json"
            existing = [
                {"market_id": "t1", "question": "Iran nuclear deal?",
                 "side": "YES", "odds": 0.1, "stake_amount": 10},
                {"market_id": "t2", "question": "Iran uranium?",
                 "side": "YES", "odds": 0.1, "stake_amount": 10},
                {"market_id": "t3", "question": "Hormuz escort?",
                 "side": "YES", "odds": 0.1, "stake_amount": 10},
            ]
            with trades_path.open("w", encoding="utf-8") as fh:
                for t in existing:
                    fh.write(json.dumps(t) + "\n")

            trade.stage_candidate(
                workspace,
                {
                    "date": "2026-04-18",
                    "market_id": "t4",
                    "question": "Will BTC close above $80,000 by April 25?",
                    "odds_yes": 0.50,
                    "odds_no": 0.50,
                    "volume": 50000,
                    "endDate": "2026-04-25T00:00:00Z",
                },
            )

            decision = decide.evaluate_staged_candidate(
                workspace, "YES", 0.70, 0.9,
                "BTC trade, different cluster — should not be capped.",
            )

            self.assertEqual(decision["action"], "trade")
            self.assertNotIn("topic_concentration_cap", decision["gate_failures"])

    def test_market_at_extreme_blocks_trade_even_with_edge(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            trade.stage_candidate(
                workspace,
                {
                    "date": "2026-04-18",
                    "market_id": "999",
                    "question": "Will BTC be above $1?",
                    "odds_yes": 0.9995,
                    "odds_no": 0.0005,
                    "volume": 50000,
                    "endDate": "2026-04-19T00:00:00Z",
                },
            )

            decision = decide.evaluate_staged_candidate(
                workspace,
                "YES",
                0.9999,
                0.95,
                "Whale says certainty but market already has it priced.",
            )

            self.assertEqual(decision["action"], "skip")
            self.assertIn("market_at_extreme", decision["gate_failures"])

    def test_extreme_delta_blocks_trade_with_fewer_than_3_whales(self):
        """|model_p - market_p| > 0.5 is model miscalibration, not edge, unless many whales agree."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            trade.stage_candidate(
                workspace,
                {
                    "date": "2026-04-19",
                    "market_id": "m-extreme",
                    "question": "Will an unlikely geopolitical event happen by April 30?",
                    "odds_yes": 0.30,
                    "odds_no": 0.70,
                    "volume": 50000,
                    "endDate": "2026-04-30T00:00:00Z",
                    "copy_strategy": {
                        "consensus_probability_yes": 0.85,
                        "confidence": 0.8,
                        "traders_with_matching_positions": 2,
                    },
                },
            )

            decision = decide.evaluate_staged_candidate(
                workspace,
                "YES",
                0.85,
                0.95,
                "Model 85 vs market 30 — 55pp delta. Almost certainly the model is wrong.",
            )

            self.assertEqual(decision["action"], "skip")
            self.assertIn("model_market_extreme_delta", decision["gate_failures"])

    def test_extreme_delta_allowed_when_at_least_3_whales_match(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            trade.stage_candidate(
                workspace,
                {
                    "date": "2026-04-19",
                    "market_id": "m-extreme-whaled",
                    "question": "Will a crypto price milestone hit by April 30?",
                    "odds_yes": 0.30,
                    "odds_no": 0.70,
                    "volume": 50000,
                    "endDate": "2026-04-30T00:00:00Z",
                    "copy_strategy": {
                        "consensus_probability_yes": 0.85,
                        "confidence": 0.8,
                        "traders_with_matching_positions": 3,
                    },
                },
            )

            decision = decide.evaluate_staged_candidate(
                workspace,
                "YES",
                0.85,
                0.95,
                "Same 55pp delta but 3 whales stacked YES — treat as real edge.",
            )

            self.assertEqual(decision["action"], "trade")
            self.assertNotIn("model_market_extreme_delta", decision["gate_failures"])

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

    def test_bonding_copy_allows_small_edge_and_caps_stake(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self.stage_candidate_bonding(workspace)

            decision = decide.evaluate_staged_candidate(
                workspace,
                "YES",
                0.99,
                0.6,
                "Bonding copy setup: near-resolution, high-confidence copy traders aligned.",
            )

            self.assertEqual(decision["action"], "trade")
            self.assertLessEqual(decision["stake_fraction"], 0.01)
            self.assertNotIn("edge_below_threshold", decision["gate_failures"])

    def test_bonding_copy_allows_half_percent_edge_for_evaluation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self.stage_candidate_bonding(workspace)

            decision = decide.evaluate_staged_candidate(
                workspace,
                "YES",
                0.985,
                0.6,
                "Bonding evaluation mode accepts thinner edge for sample collection.",
            )

            self.assertEqual(decision["action"], "trade")
            self.assertAlmostEqual(decision["edge"], 0.005, places=4)
            self.assertNotIn("edge_below_threshold", decision["gate_failures"])


if __name__ == "__main__":
    unittest.main()

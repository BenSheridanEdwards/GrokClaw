import json
import os
import tempfile
import unittest
from pathlib import Path

from tools import _polymarket_ledger as ledger


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as h:
        for r in rows:
            h.write(json.dumps(r) + "\n")


class WalletStatsTests(unittest.TestCase):
    def test_cold_start_weight_is_near_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = ledger.wallet_blend_weight("0xabc", workspace_root=tmp)
            # Beta(2,2) cold start → posterior mean 0.5 → weight = 0.20 + 0.65*0.5 = 0.525
            self.assertAlmostEqual(w, 0.525, places=3)

    def test_winning_wallet_weight_grows(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = [
                {"market_id": str(i), "won": True, "wallets": ["0xabc"], "pnl_amount": 5}
                for i in range(8)
            ]
            _write_jsonl(Path(tmp) / "data" / "polymarket-results.json", results)
            w = ledger.wallet_blend_weight("0xabc", workspace_root=tmp)
            self.assertGreater(w, 0.7)

    def test_losing_wallet_weight_shrinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = [
                {"market_id": str(i), "won": False, "wallets": ["0xdef"], "pnl_amount": -5}
                for i in range(8)
            ]
            _write_jsonl(Path(tmp) / "data" / "polymarket-results.json", results)
            w = ledger.wallet_blend_weight("0xdef", workspace_root=tmp)
            self.assertLess(w, 0.35)


class SourceKillSwitchTests(unittest.TestCase):
    def test_no_kill_with_few_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = [
                {"market_id": str(i), "won": False, "selection_source": "whale_top_trader_copy", "pnl_amount": -10}
                for i in range(2)
            ]
            _write_jsonl(Path(tmp) / "data" / "polymarket-results.json", results)
            self.assertEqual(ledger.source_stake_multiplier("whale_top_trader_copy", workspace_root=tmp), 1.0)

    def test_kill_active_when_winrate_below_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = [
                {"market_id": str(i), "won": (i < 1), "selection_source": "whale_top_trader_copy", "pnl_amount": -10}
                for i in range(5)
            ]
            _write_jsonl(Path(tmp) / "data" / "polymarket-results.json", results)
            self.assertEqual(ledger.source_stake_multiplier("whale_top_trader_copy", workspace_root=tmp), 0.5)

    def test_kill_clears_when_recent_winrate_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_losses = [
                {"market_id": f"old{i}", "won": False, "selection_source": "bonding_copy", "pnl_amount": -10}
                for i in range(15)
            ]
            recent_wins = [
                {"market_id": f"new{i}", "won": True, "selection_source": "bonding_copy", "pnl_amount": 10}
                for i in range(10)
            ]
            _write_jsonl(Path(tmp) / "data" / "polymarket-results.json", old_losses + recent_wins)
            self.assertEqual(ledger.source_stake_multiplier("bonding_copy", workspace_root=tmp), 1.0)


class SimilarityGateTests(unittest.TestCase):
    def test_no_multiplier_without_similar_losses(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                ledger.similarity_stake_multiplier("Iran nuclear deal April", "whale_top_trader_copy", workspace_root=tmp),
                1.0,
            )

    def test_halves_stake_when_two_token_overlapping_losses_on_same_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = [
                {
                    "market_id": "a",
                    "won": False,
                    "selection_source": "whale_top_trader_copy",
                    "question": "Iran nuclear deal by April 30",
                    "pnl_amount": -10,
                },
                {
                    "market_id": "b",
                    "won": False,
                    "selection_source": "whale_top_trader_copy",
                    "question": "Iran nuclear inspectors April",
                    "pnl_amount": -10,
                },
            ]
            _write_jsonl(Path(tmp) / "data" / "polymarket-results.json", results)
            mul = ledger.similarity_stake_multiplier(
                "Iran nuclear deal extended April",
                "whale_top_trader_copy",
                workspace_root=tmp,
            )
            self.assertEqual(mul, 0.5)


class CalibrationTests(unittest.TestCase):
    def test_no_shrink_below_min_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            mul, info = ledger.calibration_multiplier(workspace_root=tmp)
            self.assertEqual(mul, 1.0)
            self.assertFalse(info["applied"])

    def test_shrink_active_when_predictions_systematically_wrong(self):
        with tempfile.TemporaryDirectory() as tmp:
            # 25 trades all predicted 90% YES but only 30% won
            results = [
                {
                    "market_id": str(i),
                    "won": (i < 8),
                    "side": "YES",
                    "probability_yes": 0.90,
                    "pnl_amount": 0,
                }
                for i in range(25)
            ]
            _write_jsonl(Path(tmp) / "data" / "polymarket-results.json", results)
            mul, info = ledger.calibration_multiplier(workspace_root=tmp)
            self.assertEqual(mul, 0.80)
            self.assertTrue(info["applied"])
            self.assertGreater(info["avg_error"], 0.15)


if __name__ == "__main__":
    unittest.main()

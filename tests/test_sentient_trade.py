#!/usr/bin/env python3
"""Unit tests for Sentient trade module."""
import json
import os
import tempfile
import unittest
from pathlib import Path

# Add workspace to path
WORKSPACE = Path(__file__).resolve().parent.parent
import sys

sys.path.insert(0, str(WORKSPACE))

from tools import _sentient_trade as trade
from tools import _sentient_metrics as metrics


class SentientTradeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.data = Path(self.tmp) / "data"
        self.data.mkdir(exist_ok=True)

    def test_market_matches_model_arena(self):
        self.assertTrue(trade.market_matches_model_arena({"question": "Grok vs Claude arena"}))
        self.assertTrue(trade.market_matches_model_arena({"question": "Will GPT-5 win?"}))
        self.assertFalse(trade.market_matches_model_arena({"question": "Will it rain?"}))

    def test_get_already_evaluated_ids_empty(self):
        ids = trade.get_already_evaluated_ids(self.tmp)
        self.assertEqual(ids, set())

    def test_log_and_load_trade(self):
        trade.log_trade(
            self.tmp,
            "m1",
            "Test question?",
            "YES",
            0.6,
            "reasoning",
        )
        trades_path = self.data / "sentient-trades.json"
        self.assertTrue(trades_path.exists())
        with open(trades_path) as f:
            lines = [l for l in f if l.strip()]
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual(entry["market_id"], "m1")
        self.assertEqual(entry["side"], "YES")
        self.assertEqual(entry["odds"], 0.6)

    def test_stage_and_load_candidate(self):
        candidate = {"market_id": "m1", "question": "Q?", "odds_yes": 0.5, "odds_no": 0.5}
        trade.stage_candidate(self.tmp, candidate)
        loaded = trade.load_staged_candidate(self.tmp)
        self.assertEqual(loaded["market_id"], "m1")
        trade.clear_staged_candidate(self.tmp)
        self.assertIsNone(trade.load_staged_candidate(self.tmp))


if __name__ == "__main__":
    unittest.main()

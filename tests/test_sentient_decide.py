#!/usr/bin/env python3
"""Unit tests for Sentient decide module."""
import json
import tempfile
import unittest
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
import sys

sys.path.insert(0, str(WORKSPACE))

from tools import _sentient_decide as decide
from tools import _sentient_trade as trade
from tools import _sentient_metrics as metrics


class SentientDecideTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        data = Path(self.tmp) / "data"
        data.mkdir(exist_ok=True)
        self.candidate = {
            "market_id": "m1",
            "question": "Test?",
            "odds_yes": 0.4,
            "odds_no": 0.6,
        }
        trade.stage_candidate(self.tmp, self.candidate)

    def test_trade_passes_when_edge_above_5pct(self):
        # model 0.50 vs market 0.40 YES => edge 0.10
        record = decide.evaluate_staged_candidate(
            self.tmp, "YES", 0.50, 0.60, "Edge 10%"
        )
        self.assertEqual(record["action"], "trade")
        self.assertEqual(record["edge"], 0.1)
        trades = metrics.load_jsonl(Path(self.tmp) / "data" / "sentient-trades.json")
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]["side"], "YES")

    def test_skip_when_edge_below_5pct(self):
        trade.stage_candidate(self.tmp, self.candidate)
        record = decide.evaluate_staged_candidate(
            self.tmp, "YES", 0.44, 0.60, "Edge 4%"
        )
        self.assertEqual(record["action"], "skip")
        self.assertIn("edge_below_5pct", record["gate_failures"])
        self.assertFalse((Path(self.tmp) / "data" / "sentient-pending-trade.json").exists())


if __name__ == "__main__":
    unittest.main()

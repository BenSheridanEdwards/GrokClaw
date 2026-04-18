"""Tests for tools/_polymarket_topics.py — question topic classification."""
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools import _polymarket_topics as topics


class ClassifyQuestionTests(unittest.TestCase):
    def test_iran_us_cluster_catches_iran_questions(self):
        for q in [
            "Iran agrees to surrender enriched uranium stockpile by June 30, 2026?",
            "US-Iran nuclear deal by April 30?",
            "US escorts commercial ship through Hormuz by April 15?",
            "US x Iran diplomatic meeting by April 18, 2026?",
            "Will Trump agree to Iranian transit fees in the Strait of Hormuz in April?",
        ]:
            with self.subTest(q=q):
                self.assertEqual(topics.classify_question(q), "iran_us")

    def test_btc_cluster_catches_bitcoin_questions(self):
        self.assertEqual(
            topics.classify_question("Will the price of Bitcoin be above $74,000 on April 21?"),
            "btc_crypto",
        )
        self.assertEqual(
            topics.classify_question("Will BTC reach $82,000 on April 17?"),
            "btc_crypto",
        )

    def test_russia_ukraine_cluster(self):
        self.assertEqual(
            topics.classify_question("Russia-Ukraine ceasefire by May 1?"),
            "russia_ukraine",
        )

    def test_no_match_returns_none(self):
        self.assertIsNone(topics.classify_question("Will the new Star Wars movie be good?"))
        self.assertIsNone(topics.classify_question(""))
        self.assertIsNone(topics.classify_question(None))  # type: ignore[arg-type]


class OpenExposureByClusterTests(unittest.TestCase):
    def test_counts_open_trades_per_cluster(self):
        trades = [
            {"market_id": "a", "question": "Iran nuclear deal?"},
            {"market_id": "b", "question": "BTC above $70k?"},
            {"market_id": "c", "question": "Hormuz escort?"},
            {"market_id": "d", "question": "Star Wars quality?"},
        ]
        results = [{"market_id": "c"}]  # c resolved, so only a, b, d still open
        counts = topics.open_clusters_from_ledger(trades, results)
        self.assertEqual(counts.get("iran_us"), 1)  # a
        self.assertEqual(counts.get("btc_crypto"), 1)  # b
        self.assertNotIn("russia_ukraine", counts)

    def test_resolved_trades_do_not_count(self):
        trades = [{"market_id": "a", "question": "Iran deal?"}]
        results = [{"market_id": "a"}]
        counts = topics.open_clusters_from_ledger(trades, results)
        self.assertEqual(counts, {})


if __name__ == "__main__":
    unittest.main()

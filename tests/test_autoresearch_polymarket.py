"""Tests for autoresearch-polymarket discovery (no network)."""
import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(WORKSPACE, "skills", "autoresearch-polymarket")
if SKILL not in sys.path:
    sys.path.insert(0, SKILL)

from discovery import (  # noqa: E402
    StrategyWeights,
    binary_yes_no_market,
    pick_side_evolved,
    score_market,
    winning_label,
)


class TestAutoresearchPolymarket(unittest.TestCase):
    def test_binary_yes_no(self):
        m_ok = {"outcomes": '["Yes", "No"]', "outcomePrices": '["1", "0"]'}
        self.assertTrue(binary_yes_no_market(m_ok))
        m_bad = {"outcomes": '["A", "B"]'}
        self.assertFalse(binary_yes_no_market(m_bad))

    def test_winning_label(self):
        m = {
            "outcomes": '["Yes", "No"]',
            "outcomePrices": '["0", "1"]',
        }
        self.assertEqual(winning_label(m), "NO")

    def test_evolved_can_differ_from_always_yes(self):
        low = {
            "question": "unrelated sports fixture",
            "description": "",
            "outcomes": '["Yes", "No"]',
            "volumeNum": 10,
            "endDate": "2099-01-01T00:00:00Z",
        }
        mid = {
            "question": "Will russia test election bitcoin?",
            "description": "",
            "outcomes": '["Yes", "No"]',
            "volumeNum": 1000,
            "endDate": "2099-01-02T00:00:00Z",
        }
        high = {
            "question": "Will tariff inflation cut fed rate?",
            "description": "",
            "outcomes": '["Yes", "No"]',
            "volumeNum": 100000,
            "endDate": "2099-01-03T00:00:00Z",
        }
        markets = [low, mid, high]
        w = StrategyWeights(side_threshold=0.0, w_category=2.0, w_volume=2.0)
        med = sorted(score_market(m, w) for m in markets)[len(markets) // 2]
        s_low = pick_side_evolved(low, w, score_median=med)
        s_high = pick_side_evolved(high, w, score_median=med)
        self.assertEqual(s_low, "NO")
        self.assertEqual(s_high, "YES")
import unittest
from datetime import datetime, timedelta, timezone

from tools import _polymarket_resolve as resolve


class PolymarketResolveTests(unittest.TestCase):
    def test_get_winning_index_requires_final_one_hot_prices(self):
        self.assertEqual(resolve.get_winning_index({"outcomePrices": '["1", "0"]'}), 0)
        self.assertEqual(resolve.get_winning_index({"outcomePrices": '["0", "1"]'}), 1)
        self.assertIsNone(resolve.get_winning_index({"outcomePrices": '["0.95", "0.05"]'}))

    def test_market_is_resolved_only_when_closed_and_winner_known(self):
        self.assertTrue(resolve.market_is_resolved({"closed": True, "outcomePrices": '["1", "0"]'}))
        self.assertFalse(resolve.market_is_resolved({"closed": False, "outcomePrices": '["1", "0"]'}))
        self.assertFalse(resolve.market_is_resolved({"closed": True, "outcomePrices": '["0.6", "0.4"]'}))

    def test_pnl_rejects_invalid_odds(self):
        for bad_odds in (0, -1, 1.2):
            with self.assertRaises(ValueError):
                resolve.pnl(bad_odds, True)

    def test_grace_period_resolution_when_decisive_and_past_end(self):
        now = datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc)
        past_end = (now - timedelta(hours=48)).isoformat().replace("+00:00", "Z")
        market = {
            "closed": False,
            "endDate": past_end,
            "outcomePrices": '["0.004", "0.996"]',
        }
        self.assertTrue(resolve.market_is_resolved(market, now=now))
        self.assertEqual(resolve.get_winning_side(market, now=now), "NO")

    def test_grace_period_does_not_resolve_within_grace_window(self):
        now = datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc)
        recent_end = (now - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
        market = {
            "closed": False,
            "endDate": recent_end,
            "outcomePrices": '["0.004", "0.996"]',
        }
        self.assertFalse(resolve.market_is_resolved(market, now=now))

    def test_grace_period_does_not_resolve_when_price_not_decisive(self):
        now = datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc)
        past_end = (now - timedelta(hours=72)).isoformat().replace("+00:00", "Z")
        market = {
            "closed": False,
            "endDate": past_end,
            "outcomePrices": '["0.6", "0.4"]',
        }
        self.assertFalse(resolve.market_is_resolved(market, now=now))


if __name__ == "__main__":
    unittest.main()

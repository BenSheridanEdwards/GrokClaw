import unittest

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


if __name__ == "__main__":
    unittest.main()

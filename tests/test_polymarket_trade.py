import json
import math
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from datetime import datetime, timedelta, timezone

from tools import _polymarket_metrics as metrics
from tools import _polymarket_trade as trade


class PolymarketTradeTests(unittest.TestCase):
    def test_validate_odds_rejects_non_finite_or_out_of_range_values(self):
        for bad_value in ("0", "-0.1", "1.5", "nan", "abc"):
            with self.assertRaises(ValueError):
                trade.validate_odds(bad_value)

        self.assertTrue(math.isclose(trade.validate_odds("0.72"), 0.72))

    def test_stage_then_record_trade_uses_pending_candidate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            candidate = {
                "date": "2026-03-14",
                "market_id": "123",
                "question": "Will X happen?",
                "odds_yes": 0.72,
                "odds_no": 0.28,
            }

            trade.stage_candidate(workspace, candidate)
            trade.log_staged_trade(workspace, "YES", "high conviction")

            trades_path = workspace / "data" / "polymarket-trades.json"
            pending_path = workspace / "data" / "polymarket-pending-trade.json"

            with trades_path.open(encoding="utf-8") as handle:
                entries = [json.loads(line) for line in handle if line.strip()]

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["market_id"], "123")
            self.assertEqual(entries[0]["side"], "YES")
            self.assertEqual(entries[0]["odds"], 0.72)
            self.assertFalse(pending_path.exists())

    def test_fetch_mode_uses_explicit_workspace_argument(self):
        self.assertEqual(
            trade.resolve_workspace_root(["prog", "/tmp/custom-workspace"]),
            "/tmp/custom-workspace",
        )

    def test_already_decided_today_detects_prior_skip_or_trade(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            metrics.append_jsonl(
                workspace / "data" / "polymarket-decisions.json",
                {"date": "2026-03-14", "action": "skip"},
            )

            original_datetime = trade.datetime
            class FixedDateTime:
                @staticmethod
                def now(_tz):
                    return original_datetime(2026, 3, 14, tzinfo=_tz)
            trade.datetime = FixedDateTime
            try:
                self.assertTrue(trade.already_decided_today(workspace))
            finally:
                trade.datetime = original_datetime

    def test_get_already_evaluated_ids_excludes_markets_skipped_today(self):
        """Stop hourly cron from re-evaluating a market it already skipped the same UTC day."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            metrics.append_jsonl(
                str(workspace / "data" / "polymarket-decisions.json"),
                {"date": today, "market_id": "SKIP-M", "action": "skip"},
            )
            excluded = trade.get_already_evaluated_ids(str(workspace), days=2)
            self.assertIn("skip-m", excluded)

    def test_get_already_evaluated_ids_ignores_skip_from_prior_day(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            yesterday = (datetime.now(timezone.utc) - timedelta(days=2)).strftime(
                "%Y-%m-%d"
            )
            metrics.append_jsonl(
                str(workspace / "data" / "polymarket-decisions.json"),
                {"date": yesterday, "market_id": "OLD-SKIP", "action": "skip"},
            )
            excluded = trade.get_already_evaluated_ids(str(workspace), days=2)
            self.assertNotIn("old-skip", excluded)

    def test_fetch_markets_pages_until_empty_result(self):
        responses = [
            [{"id": "page-1"}],
            [{"id": "page-2"}],
            [],
        ]

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        call_urls = []

        def fake_urlopen(request, timeout):
            self.assertEqual(timeout, 30)
            call_urls.append(request.full_url)
            payload = responses[len(call_urls) - 1]
            return FakeResponse(json.dumps(payload).encode("utf-8"))

        with mock.patch.object(trade.urllib.request, "urlopen", side_effect=fake_urlopen):
            with mock.patch.object(trade.json, "load", side_effect=lambda resp: json.loads(resp.payload.decode("utf-8"))):
                markets = trade.fetch_markets(page_size=1, max_pages=5)

        self.assertEqual([market["id"] for market in markets], ["page-1", "page-2"])
        self.assertIn("offset=0", call_urls[0])
        self.assertIn("offset=1", call_urls[1])
        self.assertIn("offset=2", call_urls[2])

    def test_build_copy_signal_aggregates_top_trader_positions(self):
        with mock.patch.object(
            trade,
            "fetch_top_traders",
            return_value=[
                {"proxyWallet": "0xaaa", "rank": "1"},
                {"proxyWallet": "0xbbb", "rank": "2"},
            ],
        ):
            def fake_positions(wallet, condition_id=None, limit=100):
                self.assertEqual(condition_id, "0xcondition")
                if wallet == "0xaaa":
                    return [{"conditionId": "0xcondition", "outcome": "Yes", "currentValue": 1200}]
                return [{"conditionId": "0xcondition", "outcome": "No", "currentValue": 800}]

            with mock.patch.object(trade, "fetch_positions_for_user", side_effect=fake_positions):
                signal = trade.build_copy_signal("0xcondition", "Will X happen?")

        self.assertEqual(signal["status"], "ok")
        self.assertEqual(signal["consensus_side"], "YES")
        self.assertGreater(signal["consensus_probability_yes"], 0.5)
        self.assertEqual(signal["traders_with_matching_positions"], 2)

    def test_build_copy_signal_returns_unavailable_without_condition_id(self):
        signal = trade.build_copy_signal("", "Will X happen?")
        self.assertEqual(signal["status"], "unavailable")
        self.assertEqual(signal["reason"], "missing_condition_id")

    def test_select_copy_candidate_prefers_trader_backed_market(self):
        soon = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        markets = [
            {
                "id": "m1",
                "conditionId": "0xabc",
                "question": "Will Bitcoin reach $100k by end of 2026?",
                "endDate": soon,
                "outcomePrices": ["0.55", "0.45"],
                "volume": "100000",
            },
            {
                "id": "m2",
                "conditionId": "0xdef",
                "question": "Will Russia-Ukraine ceasefire happen in 2026?",
                "endDate": soon,
                "outcomePrices": ["0.40", "0.60"],
                "volume": "120000",
            },
        ]

        with mock.patch.object(
            trade,
            "fetch_top_traders",
            return_value=[
                {"proxyWallet": "0xaaa", "rank": "1"},
                {"proxyWallet": "0xbbb", "rank": "2"},
            ],
        ):
            def fake_positions(wallet, condition_id=None, limit=100):
                if wallet == "0xaaa":
                    return [{"conditionId": "0xabc", "outcome": "Yes", "currentValue": 1500}]
                return [{"conditionId": "0xabc", "outcome": "No", "currentValue": 800}]

            with mock.patch.object(trade, "fetch_positions_for_user", side_effect=fake_positions):
                best_market, signal = trade.select_copy_candidate(markets)

        self.assertIsNotNone(best_market)
        self.assertEqual(best_market["conditionId"], "0xabc")
        self.assertIsNotNone(signal)
        self.assertEqual(signal["status"], "ok")
        self.assertEqual(signal["traders_with_matching_positions"], 2)

    def test_select_bonding_copy_candidate_prefers_near_resolution_high_probability(self):
        soon = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
        later = (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
        markets = [
            {
                "id": "m-bond",
                "conditionId": "0xbond",
                "question": "Will BTC close above 120k this week?",
                "endDate": soon,
                "outcomePrices": ["0.98", "0.02"],
                "volume": "20000",
            },
            {
                "id": "m-far",
                "conditionId": "0xfar",
                "question": "Will ETH hit 10k this year?",
                "endDate": later,
                "outcomePrices": ["0.99", "0.01"],
                "volume": "20000",
            },
        ]

        with mock.patch.object(
            trade,
            "fetch_bonding_traders",
            return_value=[
                {"proxyWallet": "0x751a2b86cab503496efd325c8344e10159349ea1", "rank": "1"},
                {"proxyWallet": "0xd1c769317bd15de7768a70d0214cf0bbcc531d2b", "rank": "2"},
            ],
        ):
            def fake_positions(wallet, condition_id=None, limit=100):
                if condition_id:
                    return []
                if wallet.startswith("0x751a"):
                    return [{"conditionId": "0xbond", "outcome": "Yes", "currentValue": 2000, "title": "Will BTC close above 120k this week?"}]
                return [{"conditionId": "0xbond", "outcome": "Yes", "currentValue": 1200, "title": "Will BTC close above 120k this week?"}]

            with mock.patch.object(trade, "fetch_positions_for_user", side_effect=fake_positions):
                best_market, signal = trade.select_bonding_copy_candidate(markets)

        self.assertIsNotNone(best_market)
        self.assertEqual(best_market["conditionId"], "0xbond")
        self.assertIsNotNone(signal)
        self.assertEqual(signal["status"], "ok")
        self.assertGreaterEqual(signal["consensus_probability_yes"], 0.97)

    def test_select_bonding_copy_candidate_avoids_15_minute_markets(self):
        soon = (datetime.now(timezone.utc) + timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
        markets = [
            {
                "id": "m-latency",
                "conditionId": "0xlatency",
                "question": "Will BTC be above 120k in the next 15 minutes?",
                "endDate": soon,
                "outcomePrices": ["0.99", "0.01"],
                "volume": "50000",
            }
        ]

        with mock.patch.object(
            trade,
            "fetch_bonding_traders",
            return_value=[
                {"proxyWallet": "0x751a2b86cab503496efd325c8344e10159349ea1", "rank": "1"},
            ],
        ):
            with mock.patch.object(
                trade,
                "fetch_positions_for_user",
                return_value=[{"conditionId": "0xlatency", "outcome": "Yes", "currentValue": 3000, "title": "Will BTC be above 120k in the next 15 minutes?"}],
            ):
                best_market, signal = trade.select_bonding_copy_candidate(markets)

        self.assertIsNone(best_market)
        self.assertIsNone(signal)

    def test_select_bonding_copy_candidate_rejects_single_wallet_alignment(self):
        """A single matching whale is noise — require ≥2 wallet consensus."""
        soon = (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
        markets = [
            {
                "id": "m-single",
                "conditionId": "0xsingle",
                "question": "Will BTC close above 120k this week?",
                "endDate": soon,
                "outcomePrices": ["0.98", "0.02"],
                "volume": "18000",
            }
        ]

        with mock.patch.object(
            trade,
            "fetch_bonding_traders",
            return_value=[
                {"proxyWallet": "0x751a2b86cab503496efd325c8344e10159349ea1", "rank": "1"},
                {"proxyWallet": "0xd1c769317bd15de7768a70d0214cf0bbcc531d2b", "rank": "2"},
            ],
        ):
            def fake_positions(wallet, condition_id=None, limit=100):
                if condition_id:
                    return []
                if wallet.startswith("0x751a"):
                    return [{"conditionId": "0xsingle", "outcome": "Yes", "currentValue": 2200, "title": "Will BTC close above 120k this week?"}]
                return []

            with mock.patch.object(trade, "fetch_positions_for_user", side_effect=fake_positions):
                best_market, signal = trade.select_bonding_copy_candidate(markets)

        self.assertIsNone(best_market)
        self.assertIsNone(signal)

    def test_select_bonding_copy_candidate_accepts_two_wallet_alignment(self):
        """Two wallets agreeing on the same outcome is the minimum real consensus."""
        soon = (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
        markets = [
            {
                "id": "m-pair",
                "conditionId": "0xpair",
                "question": "Will BTC close above 120k this week?",
                "endDate": soon,
                "outcomePrices": ["0.98", "0.02"],
                "volume": "18000",
            }
        ]

        with mock.patch.object(
            trade,
            "fetch_bonding_traders",
            return_value=[
                {"proxyWallet": "0x751a2b86cab503496efd325c8344e10159349ea1", "rank": "1"},
                {"proxyWallet": "0xd1c769317bd15de7768a70d0214cf0bbcc531d2b", "rank": "2"},
            ],
        ):
            def fake_positions(wallet, condition_id=None, limit=100):
                if condition_id:
                    return []
                pos = [{"conditionId": "0xpair", "outcome": "Yes", "currentValue": 2200, "title": "Will BTC close above 120k this week?"}]
                return pos

            with mock.patch.object(trade, "fetch_positions_for_user", side_effect=fake_positions):
                best_market, signal = trade.select_bonding_copy_candidate(markets)

        self.assertIsNotNone(best_market)
        self.assertEqual(best_market["conditionId"], "0xpair")
        self.assertEqual(signal["traders_with_matching_positions"], 2)

    def test_select_bonding_copy_candidate_accepts_100c_price_boundary(self):
        soon = (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
        markets = [
            {
                "id": "m-boundary",
                "conditionId": "0xboundary",
                "question": "Will BTC close above 120k this week?",
                "endDate": soon,
                "outcomePrices": ["1.00", "0.00"],
                "volume": "18000",
            }
        ]

        with mock.patch.object(
            trade,
            "fetch_bonding_traders",
            return_value=[
                {"proxyWallet": "0x751a2b86cab503496efd325c8344e10159349ea1", "rank": "1"},
                {"proxyWallet": "0xd1c769317bd15de7768a70d0214cf0bbcc531d2b", "rank": "2"},
            ],
        ):
            with mock.patch.object(
                trade,
                "fetch_positions_for_user",
                return_value=[
                    {
                        "conditionId": "0xboundary",
                        "outcome": "Yes",
                        "currentValue": 3000,
                        "title": "Will BTC close above 120k this week?",
                    }
                ],
            ):
                best_market, signal = trade.select_bonding_copy_candidate(markets)

        self.assertIsNotNone(best_market)
        self.assertEqual(best_market["conditionId"], "0xboundary")
        self.assertIsNotNone(signal)
        self.assertGreaterEqual(signal["consensus_side_price"], 0.99)

    def test_select_bonding_copy_candidate_accepts_95c_floor_for_evaluation(self):
        soon = (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
        markets = [
            {
                "id": "m-floor",
                "conditionId": "0xfloor",
                "question": "Will BTC close above 120k this week?",
                "endDate": soon,
                "outcomePrices": ["0.95", "0.05"],
                "volume": "18000",
            }
        ]

        with mock.patch.object(
            trade,
            "fetch_bonding_traders",
            return_value=[
                {"proxyWallet": "0x751a2b86cab503496efd325c8344e10159349ea1", "rank": "1"},
                {"proxyWallet": "0xd1c769317bd15de7768a70d0214cf0bbcc531d2b", "rank": "2"},
            ],
        ):
            with mock.patch.object(
                trade,
                "fetch_positions_for_user",
                return_value=[
                    {
                        "conditionId": "0xfloor",
                        "outcome": "Yes",
                        "currentValue": 2600,
                        "title": "Will BTC close above 120k this week?",
                    }
                ],
            ):
                best_market, signal = trade.select_bonding_copy_candidate(markets)

        self.assertIsNotNone(best_market)
        self.assertEqual(best_market["conditionId"], "0xfloor")
        self.assertIsNotNone(signal)
        self.assertGreaterEqual(signal["consensus_side_price"], 0.95)

    def test_select_bonding_copy_candidate_accepts_30h_resolution_window(self):
        within_eval_window = (datetime.now(timezone.utc) + timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        markets = [
            {
                "id": "m-30h",
                "conditionId": "0x30h",
                "question": "Will BTC close above 120k this week?",
                "endDate": within_eval_window,
                "outcomePrices": ["0.98", "0.02"],
                "volume": "18000",
            }
        ]

        with mock.patch.object(
            trade,
            "fetch_bonding_traders",
            return_value=[
                {"proxyWallet": "0x751a2b86cab503496efd325c8344e10159349ea1", "rank": "1"},
                {"proxyWallet": "0xd1c769317bd15de7768a70d0214cf0bbcc531d2b", "rank": "2"},
            ],
        ):
            with mock.patch.object(
                trade,
                "fetch_positions_for_user",
                return_value=[
                    {
                        "conditionId": "0x30h",
                        "outcome": "Yes",
                        "currentValue": 2800,
                        "title": "Will BTC close above 120k this week?",
                    }
                ],
            ):
                best_market, signal = trade.select_bonding_copy_candidate(markets)

        self.assertIsNotNone(best_market)
        self.assertEqual(best_market["conditionId"], "0x30h")
        self.assertIsNotNone(signal)


if __name__ == "__main__":
    unittest.main()

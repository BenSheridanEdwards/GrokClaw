#!/usr/bin/env python3
"""
Polymarket resolve: check unresolved trades against API, append results.
Stdlib only. Called from polymarket-resolve.sh.
"""
import json
import math
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from tools import _polymarket_metrics as metrics

API_BASE = "https://gamma-api.polymarket.com/markets"
TRADES_FILE = "data/polymarket-trades.json"
RESULTS_FILE = "data/polymarket-results.json"


def fetch_market(market_id):
    url = f"{API_BASE}/{market_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "GrokClaw/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def parse_prices(raw_prices):
    prices = raw_prices or ["0.5", "0.5"]
    if isinstance(prices, str):
        prices = json.loads(prices) if prices.strip().startswith("[") else [prices, "0.5"]
    return [float(price) for price in prices]


def get_winning_index(market):
    prices = parse_prices(market.get("outcomePrices") or market.get("prices"))
    if len(prices) < 2:
        return None
    if prices[0] >= 0.999 and prices[1] <= 0.001:
        return 0
    if prices[1] >= 0.999 and prices[0] <= 0.001:
        return 1
    return None


def market_is_resolved(market):
    return market.get("closed") is True and get_winning_index(market) is not None


def get_winning_side(market):
    winning_index = get_winning_index(market)
    if winning_index == 0:
        return "YES"
    if winning_index == 1:
        return "NO"
    return None


def validate_odds(odds):
    value = float(odds)
    if not math.isfinite(value) or value <= 0 or value > 1:
        raise ValueError("odds must be a finite float in (0, 1]")
    return value


def pnl(odds, won):
    """WIN = (1/odds - 1) units; LOSS = -1 unit."""
    odds = validate_odds(odds)
    if won:
        return (1.0 / odds) - 1.0
    return -1.0


def main():
    if len(sys.argv) < 2:
        print("usage: _polymarket_resolve.py <workspace_root>", file=sys.stderr)
        sys.exit(1)
    workspace_root = sys.argv[1]
    trades_path = os.path.join(workspace_root, TRADES_FILE)
    results_path = os.path.join(workspace_root, RESULTS_FILE)
    os.makedirs(os.path.dirname(results_path), exist_ok=True)

    if not os.path.exists(trades_path):
        sys.exit(0)

    # Read trades, find unresolved
    trades = []
    with open(trades_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                trades.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    updated_trades = []
    resolved_count = 0
    for t in trades:
        if t.get("resolved"):
            updated_trades.append(t)
            continue
        market_id = t.get("market_id")
        market = fetch_market(market_id)
        if not market or not market_is_resolved(market):
            updated_trades.append(t)
            continue
        winning = get_winning_side(market)
        if winning is None:
            updated_trades.append(t)
            continue
        side = t.get("side", "YES")
        try:
            odds = validate_odds(t.get("odds", 0.5))
        except (TypeError, ValueError) as exc:
            print(f"Skipping trade with invalid odds for market {market_id}: {exc}", file=sys.stderr)
            updated_trades.append(t)
            continue
        won = side == winning
        pnl_val = pnl(odds, won)
        t["resolved"] = True
        t["resolved_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stake_amount = round(float(t.get("stake_amount", 1.0)), 2)
        pnl_amount = round(stake_amount * pnl_val, 2)
        bankroll_entry = metrics.record_bankroll_event(
            workspace_root,
            {
                "date": t["resolved_at"],
                "kind": "resolved_trade",
                "market_id": market_id,
                "question": t.get("question", ""),
                "delta": pnl_amount,
            },
        )
        updated_trades.append(t)
        result = {
            "date": t.get("date"),
            "resolved_at": t["resolved_at"],
            "market_id": market_id,
            "question": t.get("question"),
            "side": side,
            "odds": odds,
            "won": won,
            "winning_side": winning,
            "pnl": round(pnl_val, 4),
            "stake_amount": stake_amount,
            "pnl_amount": pnl_amount,
            "probability_yes": t.get("probability_yes"),
            "model_probability": t.get("model_probability"),
            "market_probability": t.get("market_probability"),
            "edge": t.get("edge"),
            "bankroll_before": bankroll_entry["bankroll_before"],
            "bankroll_after": bankroll_entry["bankroll_after"],
        }
        with open(results_path, "a") as f:
            f.write(json.dumps(result) + "\n")
        resolved_count += 1
        print(
            f"Resolved: {t.get('question', '')[:50]}... "
            f"{'WIN' if won else 'LOSS'} (P&L: {pnl_amount:+.2f}, bankroll: {bankroll_entry['bankroll_after']:+.2f})"
        )

    # Write back updated trades (with resolved=True)
    with open(trades_path, "w") as f:
        for t in updated_trades:
            f.write(json.dumps(t) + "\n")

    if resolved_count > 0:
        print(f"Resolved {resolved_count} trade(s), appended to {RESULTS_FILE}")


if __name__ == "__main__":
    main()

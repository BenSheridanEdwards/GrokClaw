#!/usr/bin/env python3
"""
Polymarket resolve: check unresolved trades against API, append results.
Stdlib only. Called from polymarket-resolve.sh.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

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


def is_resolved(market):
    return market.get("closed") is True


def get_winning_side(market):
    """Return 'YES' or 'NO' based on outcomePrices. Winning outcome has price ~1."""
    prices = market.get("outcomePrices") or market.get("prices") or ["0.5", "0.5"]
    if isinstance(prices, str):
        prices = json.loads(prices) if prices.strip().startswith("[") else ["0.5", "0.5"]
    if len(prices) < 2:
        return None
    p0 = float(prices[0])
    p1 = float(prices[1])
    if p0 > 0.9:
        return "YES"
    if p1 > 0.9:
        return "NO"
    return None


def pnl(odds, side, won):
    """WIN = (1/odds - 1) units; LOSS = -1 unit."""
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
        if not market or not is_resolved(market):
            updated_trades.append(t)
            continue
        winning = get_winning_side(market)
        if winning is None:
            updated_trades.append(t)
            continue
        side = t.get("side", "YES")
        odds = float(t.get("odds", 0.5))
        won = side == winning
        pnl_val = pnl(odds, side, won)
        t["resolved"] = True
        updated_trades.append(t)
        result = {
            "date": t.get("date"),
            "market_id": market_id,
            "question": t.get("question"),
            "side": side,
            "odds": odds,
            "won": won,
            "pnl": round(pnl_val, 4),
        }
        with open(results_path, "a") as f:
            f.write(json.dumps(result) + "\n")
        resolved_count += 1
        print(f"Resolved: {t.get('question', '')[:50]}... {'WIN' if won else 'LOSS'} (P&L: {pnl_val:+.2f})")

    # Write back updated trades (with resolved=True)
    with open(trades_path, "w") as f:
        for t in updated_trades:
            f.write(json.dumps(t) + "\n")

    if resolved_count > 0:
        print(f"Resolved {resolved_count} trade(s), appended to {RESULTS_FILE}")


if __name__ == "__main__":
    main()

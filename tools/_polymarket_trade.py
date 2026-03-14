#!/usr/bin/env python3
"""
Polymarket paper trade: fetch markets, select best, or log a trade.
Stdlib only. Called from polymarket-trade.sh.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

API_URL = "https://gamma-api.polymarket.com/markets"
TRADES_FILE = "data/polymarket-trades.json"


def fetch_markets():
    url = f"{API_URL}?active=true&closed=false&limit=20&order=volume&ascending=false"
    req = urllib.request.Request(url, headers={"User-Agent": "GrokClaw/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def select_market(markets):
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=7)
    best = None
    best_volume = 0
    for m in markets:
        end_str = m.get("endDate") or m.get("end_date_iso")
        if not end_str:
            continue
        try:
            end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue
        if now < end <= cutoff:
            vol = float(m.get("volume") or m.get("volumeNum") or 0)
            if vol > best_volume:
                best_volume = vol
                best = m
    return best


def log_trade(workspace_root, market_id, question, side, odds, reasoning):
    trades_path = os.path.join(workspace_root, TRADES_FILE)
    os.makedirs(os.path.dirname(trades_path), exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = {
        "date": today,
        "market_id": market_id,
        "question": question,
        "side": side,
        "odds": float(odds),
        "reasoning": reasoning,
        "resolved": False,
    }
    line = json.dumps(entry) + "\n"
    with open(trades_path, "a") as f:
        f.write(line)
    print(f"Logged trade: {question[:50]}... ({side} @ {odds})")


def already_traded_today(workspace_root):
    trades_path = os.path.join(workspace_root, TRADES_FILE)
    if not os.path.exists(trades_path):
        return False
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(trades_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("date") == today:
                    return True
            except json.JSONDecodeError:
                continue
    return False


def main():
    if len(sys.argv) == 1:
        # Fetch and select
        workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if already_traded_today(workspace_root):
            print("Already traded today, skipping.", file=sys.stderr)
            sys.exit(0)
        markets = fetch_markets()
        best = select_market(markets)
        if not best:
            print("No suitable market found (volume, closing within 7 days)", file=sys.stderr)
            sys.exit(1)
        # outcomePrices: ["0.72","0.28"] for YES, NO (may be JSON string)
        prices = best.get("outcomePrices") or best.get("prices") or ["0.5", "0.5"]
        if isinstance(prices, str):
            prices = json.loads(prices) if prices.strip().startswith("[") else [prices, "0.5"]
        odds_yes = float(prices[0]) if prices else 0.5
        odds_no = float(prices[1]) if len(prices) > 1 else 1 - odds_yes
        out = {
            "id": best.get("id") or best.get("conditionId"),
            "question": best.get("question", ""),
            "odds_yes": odds_yes,
            "odds_no": odds_no,
            "volume": best.get("volume") or best.get("volumeNum"),
            "endDate": best.get("endDate") or best.get("end_date_iso"),
        }
        print(json.dumps(out))
        return

    if len(sys.argv) >= 7:
        # Log: workspace_root market_id side odds reasoning question
        workspace_root = sys.argv[1]
        market_id = sys.argv[2]
        side = sys.argv[3]
        odds = sys.argv[4]
        reasoning = sys.argv[5]
        question = " ".join(sys.argv[6:]) if len(sys.argv) > 6 else ""
        if side not in ("YES", "NO"):
            print("side must be YES or NO", file=sys.stderr)
            sys.exit(1)
        log_trade(workspace_root, market_id, question, side, odds, reasoning)
        return

    print("usage: fetch mode (no args) or log mode: workspace_root market_id question side odds reasoning", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()

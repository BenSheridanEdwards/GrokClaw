#!/usr/bin/env python3
"""Close open paper trades when the market has moved decisively against us.

If the entry side's current market price has dropped by `drop_threshold`
relative to entry odds, we treat the trade as known-wrong and realize the
loss at the current price rather than holding to resolution. The realized
loss (partial stake) is credited to the bankroll; the trade is marked
resolved + voided with a stop_loss reason.

This is the paper-book analogue of a real-money stop-loss. The alternative —
praying for reversal — has a near-certain negative expected value because
Polymarket prices after a 30pp move rarely fully reverse.

Stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from tools import _polymarket_metrics as metrics
from tools import _polymarket_resolve as resolve
from tools import _polymarket_trade as pmtrade

DEFAULT_DROP_THRESHOLD = 0.30
TRADES_FILE = "data/polymarket-trades.json"


def current_side_price(market, side):
    prices = resolve.parse_prices(market.get("outcomePrices") or market.get("prices"))
    if len(prices) < 2:
        return None
    if side == "YES":
        return float(prices[0])
    return float(prices[1])


def run_stop_loss(
    workspace_root,
    drop_threshold=DEFAULT_DROP_THRESHOLD,
    fetch_market=None,
    now=None,
):
    fetch_market = fetch_market or pmtrade.fetch_json  # for production; tests override
    if fetch_market is pmtrade.fetch_json:
        def fetch_market(market_id):  # type: ignore[misc]
            return resolve.fetch_market(market_id)

    now = now or datetime.now(timezone.utc)
    trades_path = os.path.join(workspace_root, TRADES_FILE)
    trades = metrics.load_jsonl(trades_path)
    updated = []
    voided_ids = []

    for trade in trades:
        if trade.get("resolved"):
            updated.append(trade)
            continue
        market_id = trade.get("market_id")
        side = trade.get("side") or "YES"
        try:
            entry = float(trade.get("odds") or 0.0)
        except (TypeError, ValueError):
            entry = 0.0
        stake = float(trade.get("stake_amount") or 0.0)
        if entry <= 0 or stake <= 0:
            updated.append(trade)
            continue

        market = fetch_market(market_id) if market_id else None
        if not market:
            updated.append(trade)
            continue

        current = current_side_price(market, side)
        if current is None:
            updated.append(trade)
            continue

        if (entry - current) < drop_threshold:
            updated.append(trade)
            continue

        realized = round(stake * (current - entry) / entry, 2)
        trade["resolved"] = True
        trade["voided"] = True
        trade["resolved_at"] = now.strftime("%Y-%m-%d")
        trade["void_reason"] = "stop_loss"
        trade["stop_loss_exit_price"] = round(current, 4)
        trade["stop_loss_realized"] = realized
        updated.append(trade)
        voided_ids.append(market_id)

        metrics.record_bankroll_event(
            workspace_root,
            {
                "date": trade["resolved_at"],
                "kind": "stop_loss",
                "market_id": market_id,
                "question": trade.get("question", ""),
                "delta": realized,
            },
        )
        print(
            f"Stop-loss voided: {str(trade.get('question',''))[:60]}... "
            f"(entry {entry:.3f} → exit {current:.3f}, realized ${realized:+.2f})",
            file=sys.stderr,
        )

    if voided_ids:
        os.makedirs(os.path.dirname(trades_path), exist_ok=True)
        with open(trades_path, "w", encoding="utf-8") as fh:
            for t in updated:
                fh.write(json.dumps(t) + "\n")

    return {"voided": len(voided_ids), "voided_market_ids": voided_ids}


def main():
    workspace_root = sys.argv[1] if len(sys.argv) > 1 else WORKSPACE_ROOT
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_DROP_THRESHOLD
    summary = run_stop_loss(workspace_root, drop_threshold=threshold)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()

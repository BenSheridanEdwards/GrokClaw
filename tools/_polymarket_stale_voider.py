#!/usr/bin/env python3
"""Void stale unresolved paper trades to free up open_exposure.

The problem: when a Polymarket market stays `closed: false` days past its
stated endDate and the price never collapses to a decisive extreme, grace-
period resolution cannot settle the trade. The stake then sits in
`open_exposure` forever, eventually blocking new trades via the exposure cap.

This tool looks for unresolved trades whose endDate (or trade date if endDate
is missing) is more than `stale_hours` in the past and voids them: the stake
is credited back to the bankroll and the trade is marked `resolved=True,
voided=True` so it no longer contributes to open exposure. No win/loss is
recorded — voided trades are a no-op on PnL and calibration.

Stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from tools import _polymarket_metrics as metrics

DEFAULT_STALE_HOURS = 48
TRADES_FILE = "data/polymarket-trades.json"


def _parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _effective_end(trade):
    end = _parse_iso(trade.get("endDate"))
    if end is not None:
        return end
    return _parse_date(trade.get("date"))


def void_stale_trades(workspace_root, stale_hours=DEFAULT_STALE_HOURS, now=None):
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=stale_hours)
    trades_path = os.path.join(workspace_root, TRADES_FILE)

    trades = metrics.load_jsonl(trades_path)
    voided_ids = []
    updated = []

    for trade in trades:
        if trade.get("resolved"):
            updated.append(trade)
            continue
        effective_end = _effective_end(trade)
        if effective_end is None or effective_end > cutoff:
            updated.append(trade)
            continue

        stake = float(trade.get("stake_amount") or 0.0)
        trade["resolved"] = True
        trade["voided"] = True
        trade["resolved_at"] = now.strftime("%Y-%m-%d")
        trade["void_reason"] = f"stale_past_{stale_hours}h"

        if stake > 0:
            metrics.record_bankroll_event(
                workspace_root,
                {
                    "date": trade["resolved_at"],
                    "kind": "voided_stale_trade",
                    "market_id": trade.get("market_id"),
                    "question": trade.get("question", ""),
                    "delta": stake,
                },
            )
        voided_ids.append(trade.get("market_id"))
        updated.append(trade)
        print(
            f"Voided stale trade: {str(trade.get('question',''))[:60]}... "
            f"(stake ${stake:.2f} returned)",
            file=sys.stderr,
        )

    if voided_ids:
        os.makedirs(os.path.dirname(trades_path), exist_ok=True)
        with open(trades_path, "w", encoding="utf-8") as fh:
            for trade in updated:
                fh.write(json.dumps(trade) + "\n")

    return {"voided": len(voided_ids), "voided_market_ids": voided_ids}


def main():
    workspace_root = (
        sys.argv[1] if len(sys.argv) > 1 else WORKSPACE_ROOT
    )
    stale_hours = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_STALE_HOURS
    summary = void_stale_trades(workspace_root, stale_hours=stale_hours)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()

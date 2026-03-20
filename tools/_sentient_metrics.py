#!/usr/bin/env python3
"""
Shared helpers for Sentient (model arena) prediction market ledgers.
Paper trading only. Stdlib only.
"""
import json
import os
from datetime import datetime, timedelta, timezone

STARTING_BANKROLL = 1000.0
BANKROLL_FILE = "data/sentient-bankroll.json"
RESULTS_FILE = "data/sentient-results.json"
DECISIONS_FILE = "data/sentient-decisions.json"
SKIPS_FILE = "data/sentient-skips.json"
TRADES_FILE = "data/sentient-trades.json"

MIN_SHIFT_PERCENT = 0.05  # 5% consensus edge threshold
MAX_STAKE_FRACTION = 0.02
MAX_OPEN_EXPOSURE_FRACTION = 0.10
FRACTIONAL_KELLY = 0.25


def jsonl_path(workspace_root, relative_path):
    return os.path.join(workspace_root, relative_path)


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def append_jsonl(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def current_bankroll(workspace_root):
    bankroll_path = jsonl_path(workspace_root, BANKROLL_FILE)
    rows = load_jsonl(bankroll_path)
    if not rows:
        return STARTING_BANKROLL
    return float(rows[-1]["bankroll_after"])


def record_bankroll_event(workspace_root, event):
    bankroll_before = current_bankroll(workspace_root)
    delta = round(float(event["delta"]), 2)
    bankroll_after = round(bankroll_before + delta, 2)
    entry = {
        "date": event.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "kind": event.get("kind", "bankroll_update"),
        "market_id": event.get("market_id"),
        "question": event.get("question", ""),
        "delta": delta,
        "bankroll_before": bankroll_before,
        "bankroll_after": bankroll_after,
    }
    append_jsonl(jsonl_path(workspace_root, BANKROLL_FILE), entry)
    return entry


def unresolved_exposure(workspace_root):
    trades_path = jsonl_path(workspace_root, TRADES_FILE)
    exposure = 0.0
    for trade in load_jsonl(trades_path):
        if not trade.get("resolved"):
            exposure += float(trade.get("stake_amount", 0.0))
    return round(exposure, 2)


def summarize(workspace_root, days=None, now=None):
    now = now or datetime.now(timezone.utc)
    results = load_jsonl(jsonl_path(workspace_root, RESULTS_FILE))
    decisions = load_jsonl(jsonl_path(workspace_root, DECISIONS_FILE))
    bankroll_rows = load_jsonl(jsonl_path(workspace_root, BANKROLL_FILE))

    if days is not None:
        cutoff = now - timedelta(days=days)
        results = [r for r in results if r.get("resolved_at") and r.get("resolved_at", "") >= cutoff.strftime("%Y-%m-%d")]
        decisions = [d for d in decisions if d.get("date") and d.get("date", "") >= cutoff.strftime("%Y-%m-%d")]
        bankroll_rows = [b for b in bankroll_rows if b.get("date") and b.get("date", "") >= cutoff.strftime("%Y-%m-%d")]

    total_pnl = round(sum(float(r.get("pnl_amount", 0.0)) for r in results), 2)
    wins = sum(1 for r in results if r.get("won"))
    resolved_count = len(results)
    trade_decisions = [d for d in decisions if d.get("action") == "trade"]
    skips = [d for d in decisions if d.get("action") == "skip"]

    return {
        "current_bankroll": current_bankroll(workspace_root),
        "resolved_count": resolved_count,
        "wins": wins,
        "accuracy": (wins / resolved_count) if resolved_count else 0.0,
        "total_pnl": total_pnl,
        "skip_count": len(skips),
        "results": results,
        "decisions": decisions,
    }

#!/usr/bin/env python3
"""
Shared helpers for Polymarket ledgers, bankroll tracking, and reporting.
Stdlib only.
"""
import json
import os
from datetime import datetime, timedelta, timezone

STARTING_BANKROLL = 1000.0
BANKROLL_FILE = "data/polymarket-bankroll.json"
RESULTS_FILE = "data/polymarket-results.json"
DECISIONS_FILE = "data/polymarket-decisions.json"
SKIPS_FILE = "data/polymarket-skips.json"
TRADES_FILE = "data/polymarket-trades.json"

PROMOTION_BANKROLL_TARGET = 100000.0
PROMOTION_MIN_RESOLVED_TRADES = 200
PROMOTION_MAX_DRAWDOWN = 0.25
PROMOTION_MAX_BRIER = 0.20


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


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def filter_recent(rows, days, date_key, now):
    cutoff = now - timedelta(days=days)
    recent = []
    for row in rows:
        parsed = parse_date(row.get(date_key))
        if parsed is not None and parsed >= cutoff:
            recent.append(row)
    return recent


def scoped_bankroll_rows(rows, days, now):
    cutoff = now - timedelta(days=days)
    prior_balance = STARTING_BANKROLL
    recent = []

    for row in rows:
        parsed = parse_date(row.get("date"))
        if parsed is None:
            continue
        if parsed < cutoff:
            prior_balance = float(row.get("bankroll_after", prior_balance))
            continue
        recent.append(row)

    return recent, prior_balance


def calculate_brier(results):
    scored = []
    for result in results:
        probability_yes = result.get("probability_yes")
        if probability_yes is None:
            continue
        outcome_yes = 1.0 if result.get("winning_side") == "YES" else 0.0
        scored.append((float(probability_yes) - outcome_yes) ** 2)
    if not scored:
        return None
    return sum(scored) / len(scored)


def calculate_max_drawdown(bankroll_rows, starting_peak=STARTING_BANKROLL):
    peak = starting_peak
    max_drawdown = 0.0
    for row in bankroll_rows:
        balance = float(row.get("bankroll_after", STARTING_BANKROLL))
        if balance > peak:
            peak = balance
        if peak > 0:
            drawdown = (peak - balance) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
    return max_drawdown


def summarize(workspace_root, days=None, now=None):
    now = now or datetime.now(timezone.utc)
    results = load_jsonl(jsonl_path(workspace_root, RESULTS_FILE))
    decisions = load_jsonl(jsonl_path(workspace_root, DECISIONS_FILE))
    bankroll_rows = load_jsonl(jsonl_path(workspace_root, BANKROLL_FILE))
    drawdown_peak = STARTING_BANKROLL

    if days is not None:
        results = filter_recent(results, days, "resolved_at", now)
        decisions = filter_recent(decisions, days, "date", now)
        bankroll_rows, drawdown_peak = scoped_bankroll_rows(bankroll_rows, days, now)

    total_pnl = round(sum(float(result.get("pnl_amount", 0.0)) for result in results), 2)
    wins = sum(1 for result in results if result.get("won"))
    resolved_count = len(results)
    trade_decisions = [decision for decision in decisions if decision.get("action") == "trade"]
    skips = [decision for decision in decisions if decision.get("action") == "skip"]
    average_edge = (
        sum(float(decision.get("edge", 0.0)) for decision in trade_decisions) / len(trade_decisions)
        if trade_decisions
        else None
    )
    last100 = results[-100:]
    last100_expectancy = (
        sum(float(result.get("pnl_amount", 0.0)) for result in last100) / len(last100)
        if last100
        else 0.0
    )

    return {
        "current_bankroll": current_bankroll(workspace_root),
        "resolved_count": resolved_count,
        "wins": wins,
        "accuracy": (wins / resolved_count) if resolved_count else 0.0,
        "total_pnl": total_pnl,
        "average_edge": average_edge,
        "skip_count": len(skips),
        "brier_score": calculate_brier(results),
        "max_drawdown": calculate_max_drawdown(bankroll_rows, starting_peak=drawdown_peak),
        "last100_expectancy": last100_expectancy,
        "results": results,
        "decisions": decisions,
    }


def check_promotion_gate(summary):
    blocked_on = []
    if float(summary.get("current_bankroll", 0.0)) < PROMOTION_BANKROLL_TARGET:
        blocked_on.append("bankroll")
    if int(summary.get("resolved_count", 0)) < PROMOTION_MIN_RESOLVED_TRADES:
        blocked_on.append("resolved_count")
    if float(summary.get("last100_expectancy", 0.0)) <= 0:
        blocked_on.append("last100_expectancy")

    max_drawdown = summary.get("max_drawdown")
    if max_drawdown is None or float(max_drawdown) > PROMOTION_MAX_DRAWDOWN:
        blocked_on.append("max_drawdown")

    brier_score = summary.get("brier_score")
    if brier_score is None or float(brier_score) > PROMOTION_MAX_BRIER:
        blocked_on.append("brier_score")

    return {
        "eligible": not blocked_on,
        "blocked_on": blocked_on,
    }

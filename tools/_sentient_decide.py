#!/usr/bin/env python3
"""
Sentient decision engine: evaluate multi-model consensus against risk gates.
Bet if consensus predicts >5% shift within time window. Paper trading only.
Stdlib only. Called from sentient-decide.sh.
"""
import json
import math
import os
import sys
from datetime import datetime, timezone

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from tools import _sentient_metrics as metrics
from tools import _sentient_trade as trade

DECISIONS_FILE = "data/sentient-decisions.json"
SKIPS_FILE = "data/sentient-skips.json"

MIN_SHIFT_PERCENT = 0.05  # 5% edge threshold
MIN_CONFIDENCE = 0.55
MAX_STAKE_FRACTION = 0.02
MAX_OPEN_EXPOSURE_FRACTION = 0.10
FRACTIONAL_KELLY = 0.25


def validate_probability(value, label):
    probability = float(value)
    if not math.isfinite(probability) or probability <= 0 or probability >= 1:
        raise ValueError(f"{label} must be a finite float in (0, 1)")
    return probability


def probability_yes(side, selected_probability):
    if side == "YES":
        return selected_probability
    return 1.0 - selected_probability


def kelly_fraction(market_probability, estimated_probability):
    market_probability = validate_probability(market_probability, "market probability")
    estimated_probability = validate_probability(estimated_probability, "estimated probability")
    net_odds = (1.0 / market_probability) - 1.0
    loss_probability = 1.0 - estimated_probability
    return max(0.0, ((net_odds * estimated_probability) - loss_probability) / net_odds)


def append_decision(workspace_root, record):
    metrics.append_jsonl(metrics.jsonl_path(workspace_root, DECISIONS_FILE), record)


def append_skip(workspace_root, record):
    metrics.append_jsonl(metrics.jsonl_path(workspace_root, SKIPS_FILE), record)


def build_record(workspace_root, candidate, side, selected_probability, confidence, reasoning, bankroll_before):
    market_probability = candidate["odds_yes"] if side == "YES" else candidate["odds_no"]
    edge = selected_probability - market_probability
    raw_kelly = kelly_fraction(market_probability, selected_probability)
    stake_fraction = min(raw_kelly * FRACTIONAL_KELLY, MAX_STAKE_FRACTION)
    stake_amount = round(bankroll_before * stake_fraction, 2)
    open_exposure = metrics.unresolved_exposure(str(workspace_root))

    gate_failures = []
    if edge < MIN_SHIFT_PERCENT:
        gate_failures.append("edge_below_5pct")
    if confidence < MIN_CONFIDENCE:
        gate_failures.append("confidence_below_threshold")
    if stake_fraction <= 0:
        gate_failures.append("stake_non_positive")
    if bankroll_before > 0 and ((open_exposure + stake_amount) / bankroll_before) > MAX_OPEN_EXPOSURE_FRACTION:
        gate_failures.append("open_exposure_cap")

    action = "trade" if not gate_failures else "skip"
    return {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "market_id": candidate["market_id"],
        "question": candidate["question"],
        "side": side,
        "market_probability": round(market_probability, 4),
        "model_probability": round(selected_probability, 4),
        "probability_yes": round(probability_yes(side, selected_probability), 4),
        "confidence": round(confidence, 4),
        "edge": round(edge, 4),
        "kelly_fraction": round(raw_kelly, 4),
        "stake_fraction": round(stake_fraction, 4),
        "stake_amount": stake_amount,
        "bankroll_before": round(bankroll_before, 2),
        "open_exposure": round(open_exposure, 2),
        "reasoning": reasoning,
        "action": action,
        "gate_failures": gate_failures,
    }


def evaluate_staged_candidate(workspace_root, side, model_probability, confidence, reasoning):
    candidate = trade.load_staged_candidate(str(workspace_root))
    if candidate is None:
        raise ValueError("no staged candidate")
    if side not in ("YES", "NO"):
        raise ValueError("side must be YES or NO")

    selected_probability = validate_probability(model_probability, "model probability")
    confidence = validate_probability(confidence, "confidence")
    bankroll_before = metrics.current_bankroll(str(workspace_root))
    record = build_record(workspace_root, candidate, side, selected_probability, confidence, reasoning, bankroll_before)
    append_decision(str(workspace_root), record)

    if record["action"] == "trade":
        trade.log_trade(
            str(workspace_root),
            candidate["market_id"],
            candidate["question"],
            side,
            candidate["odds_yes"] if side == "YES" else candidate["odds_no"],
            reasoning,
            metadata={
                "market_probability": record["market_probability"],
                "model_probability": record["model_probability"],
                "probability_yes": record["probability_yes"],
                "confidence": record["confidence"],
                "edge": record["edge"],
                "kelly_fraction": record["kelly_fraction"],
                "stake_fraction": record["stake_fraction"],
                "stake_amount": record["stake_amount"],
            },
        )
        trade.clear_staged_candidate(str(workspace_root))
        return record

    append_skip(str(workspace_root), record)
    trade.clear_staged_candidate(str(workspace_root))
    return record


def record_explicit_skip(workspace_root, reasoning):
    candidate = trade.load_staged_candidate(str(workspace_root))
    if candidate is None:
        raise ValueError("no staged candidate")

    bankroll_before = metrics.current_bankroll(str(workspace_root))
    record = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "market_id": candidate["market_id"],
        "question": candidate["question"],
        "side": "SKIP",
        "market_probability": None,
        "model_probability": None,
        "probability_yes": None,
        "confidence": 0.0,
        "edge": 0.0,
        "kelly_fraction": 0.0,
        "stake_fraction": 0.0,
        "stake_amount": 0.0,
        "bankroll_before": round(bankroll_before, 2),
        "open_exposure": round(metrics.unresolved_exposure(str(workspace_root)), 2),
        "reasoning": reasoning,
        "action": "skip",
        "gate_failures": ["explicit_skip"],
    }
    append_decision(str(workspace_root), record)
    append_skip(str(workspace_root), record)
    trade.clear_staged_candidate(str(workspace_root))
    return record


def main():
    if len(sys.argv) < 3:
        print(
            "usage: _sentient_decide.py <workspace_root> SKIP <reasoning> "
            "or _sentient_decide.py <workspace_root> <side> <probability> <confidence> <reasoning>",
            file=sys.stderr,
        )
        sys.exit(1)

    workspace_root = sys.argv[1]
    mode = sys.argv[2]

    if mode == "SKIP":
        reasoning = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "No trade selected."
        print(json.dumps(record_explicit_skip(workspace_root, reasoning)))
        return

    if len(sys.argv) < 6:
        print("missing probability/confidence/reasoning", file=sys.stderr)
        sys.exit(1)

    side = mode
    model_probability = sys.argv[3]
    confidence = sys.argv[4]
    reasoning = " ".join(sys.argv[5:])
    print(json.dumps(evaluate_staged_candidate(workspace_root, side, model_probability, confidence, reasoning)))


if __name__ == "__main__":
    main()

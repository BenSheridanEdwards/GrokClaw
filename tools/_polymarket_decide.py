#!/usr/bin/env python3
"""
Evaluate a staged Polymarket candidate using Grok's estimate plus deterministic gates.
Stdlib only. Called from polymarket-decide.sh.
"""

import json
import math
import os
import sys
from datetime import datetime, timezone

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from tools import _polymarket_metrics as metrics
from tools import _polymarket_trade as trade
from tools import _polymarket_ledger as ledger
from tools import _polymarket_topics as topics

DECISIONS_FILE = "data/polymarket-decisions.json"
SKIPS_FILE = "data/polymarket-skips.json"
TRADES_FILE = "data/polymarket-trades.json"
RESULTS_FILE = "data/polymarket-results.json"

# Stop news-cycle concentration: never hold more than this many open paper
# trades in the same topic cluster (Iran/US, BTC, Russia/Ukraine, etc.).
# The failure mode we fix: the paper book had 5 Iran/US bets opened in four
# days so a single news shift on Iran tanked most of the book together.
MAX_OPEN_PER_CLUSTER = 3

MIN_EDGE = 0.05
MIN_CONFIDENCE = 0.55
MIN_VOLUME = 5000.0
MIN_VOLUME_WHALE_BACKED = 3000.0
BONDING_MIN_VOLUME = 2000.0
MAX_STAKE_FRACTION = 0.02
# 0.10 cap with 2% stakes meant 5 concurrent slots; with stuck pending trades
# the cap permanently tripped and blocked every new trade. Doubled to 20% to
# allow ~10 concurrent positions for paper-money signal density.
MAX_OPEN_EXPOSURE_FRACTION = 0.20
FRACTIONAL_KELLY = 0.25
BONDING_MIN_EDGE = 0.005
BONDING_MIN_CONFIDENCE = 0.45
BONDING_MAX_STAKE_FRACTION = 0.01
BONDING_MAX_OPEN_EXPOSURE_FRACTION = 0.16

# Refuse to trade when the market has already priced the outcome at near-certainty:
# the residual "edge" is gas/fee-loss territory, not real opportunity.
MARKET_PROBABILITY_FLOOR = 0.05
MARKET_PROBABILITY_CEILING = 0.95

# When the model disagrees with the market by more than this on the side we
# intend to trade, the most likely explanation is model miscalibration, not
# mispricing. The Iran/US resolved losses (model said 99.99% on NO-settling
# markets priced 5-50%) are the fingerprint we are filtering out.
# We exempt cases where at least this many independent whales have the same
# position — that is a strong enough signal to override the model-vs-market
# disagreement.
EXTREME_DELTA_THRESHOLD = 0.5
EXTREME_DELTA_WHALE_OVERRIDE = 3

# Calibration-unproven gate. A (topic, source) combo with a proven bad Brier
# score should not place stakes until it improves. Requires enough resolved
# samples in the same combo to draw a signal from noise.
CALIBRATION_MAX_BRIER = 0.25
CALIBRATION_REQUIRED_SAMPLES = 20


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
    estimated_probability = validate_probability(
        estimated_probability, "estimated probability"
    )
    net_odds = (1.0 / market_probability) - 1.0
    loss_probability = 1.0 - estimated_probability
    return max(0.0, ((net_odds * estimated_probability) - loss_probability) / net_odds)


def append_decision(workspace_root, record):
    metrics.append_jsonl(metrics.jsonl_path(workspace_root, DECISIONS_FILE), record)


def append_skip(workspace_root, record):
    metrics.append_jsonl(metrics.jsonl_path(workspace_root, SKIPS_FILE), record)


def build_record(
    candidate, side, selected_probability, confidence, reasoning, bankroll_before
):
    market_probability = (
        candidate["odds_yes"] if side == "YES" else candidate["odds_no"]
    )
    edge = selected_probability - market_probability
    raw_kelly = kelly_fraction(market_probability, selected_probability)
    selection_source = candidate.get("selection_source") or ""
    min_edge = MIN_EDGE
    min_confidence = MIN_CONFIDENCE
    max_stake_fraction = MAX_STAKE_FRACTION
    max_open_exposure_fraction = MAX_OPEN_EXPOSURE_FRACTION
    if selection_source == "bonding_copy":
        min_edge = BONDING_MIN_EDGE
        min_confidence = BONDING_MIN_CONFIDENCE
        max_stake_fraction = BONDING_MAX_STAKE_FRACTION
        max_open_exposure_fraction = BONDING_MAX_OPEN_EXPOSURE_FRACTION

    workspace_root = str(candidate["workspace_root"])
    source_mul = ledger.source_stake_multiplier(selection_source, workspace_root=workspace_root)
    similarity_mul = ledger.similarity_stake_multiplier(
        candidate.get("question", ""), selection_source, workspace_root=workspace_root,
    )
    feedback_multiplier = source_mul * similarity_mul
    max_stake_fraction = max_stake_fraction * feedback_multiplier

    stake_fraction = min(raw_kelly * FRACTIONAL_KELLY, max_stake_fraction)
    stake_amount = round(bankroll_before * stake_fraction, 2)
    open_exposure = metrics.unresolved_exposure(workspace_root)

    gate_failures = []
    if selection_source != "bonding_copy" and (
        market_probability < MARKET_PROBABILITY_FLOOR
        or market_probability > MARKET_PROBABILITY_CEILING
    ):
        gate_failures.append("market_at_extreme")
    if edge < min_edge:
        gate_failures.append("edge_below_threshold")
    if confidence < min_confidence:
        gate_failures.append("confidence_below_threshold")
    volume = float(candidate.get("volume", 0.0) or 0.0)
    copy_strat = candidate.get("copy_strategy") or {}
    traders = int(copy_strat.get("traders_with_matching_positions", 0) or 0)
    if selection_source == "bonding_copy":
        min_vol = BONDING_MIN_VOLUME
    else:
        min_vol = MIN_VOLUME_WHALE_BACKED if traders >= 2 else MIN_VOLUME
    if volume < min_vol:
        gate_failures.append("volume_below_threshold")
    if stake_fraction <= 0:
        gate_failures.append("stake_non_positive")
    if (
        bankroll_before > 0
        and ((open_exposure + stake_amount) / bankroll_before)
        > max_open_exposure_fraction
    ):
        gate_failures.append("open_exposure_cap")

    if (
        abs(selected_probability - market_probability) > EXTREME_DELTA_THRESHOLD
        and traders < EXTREME_DELTA_WHALE_OVERRIDE
    ):
        gate_failures.append("model_market_extreme_delta")

    if (
        side == "YES"
        and selection_source != "bonding_copy"
        and topics.is_aspirational_question(candidate.get("question"))
        and traders < EXTREME_DELTA_WHALE_OVERRIDE
    ):
        gate_failures.append("aspirational_yes_bias")

    cal_samples, cal_brier = ledger.topic_source_calibration(
        candidate.get("question", ""),
        selection_source,
        workspace_root=workspace_root,
    )
    if (
        cal_samples >= CALIBRATION_REQUIRED_SAMPLES
        and cal_brier is not None
        and cal_brier > CALIBRATION_MAX_BRIER
    ):
        gate_failures.append("calibration_unproven")

    cluster = topics.classify_question(candidate.get("question"))
    if cluster:
        trades_rows = metrics.load_jsonl(
            metrics.jsonl_path(workspace_root, TRADES_FILE)
        )
        results_rows = metrics.load_jsonl(
            metrics.jsonl_path(workspace_root, RESULTS_FILE)
        )
        open_clusters = topics.open_clusters_from_ledger(trades_rows, results_rows)
        if open_clusters.get(cluster, 0) >= MAX_OPEN_PER_CLUSTER:
            gate_failures.append("topic_concentration_cap")

    action = "trade" if not gate_failures else "skip"
    copy_strat = candidate.get("copy_strategy") or {}
    wallets = []
    for sample in (copy_strat.get("samples") or []):
        wallet = sample.get("wallet") if isinstance(sample, dict) else None
        if wallet:
            wallets.append(str(wallet).lower())
    wallets = sorted(set(wallets))
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
        "volume": float(candidate.get("volume", 0.0) or 0.0),
        "whale_consensus_probability": copy_strat.get("consensus_probability_yes"),
        "whale_confidence": copy_strat.get("confidence"),
        "whale_traders": copy_strat.get("traders_with_matching_positions"),
        "selection_source": candidate.get("selection_source"),
        "strategy_profile": "bonding_copy" if selection_source == "bonding_copy" else "default",
        "wallets": wallets,
        "source_stake_multiplier": round(source_mul, 4),
        "similarity_stake_multiplier": round(similarity_mul, 4),
        "feedback_multiplier": round(feedback_multiplier, 4),
        "reasoning": reasoning,
        "action": action,
        "gate_failures": gate_failures,
    }


def evaluate_staged_candidate(
    workspace_root, side, model_probability, confidence, reasoning
):
    candidate = trade.load_staged_candidate(str(workspace_root))
    if candidate is None:
        raise ValueError("no staged candidate for today")
    if side not in ("YES", "NO"):
        raise ValueError("side must be YES or NO")

    selected_probability = validate_probability(model_probability, "model probability")
    confidence = validate_probability(confidence, "confidence")
    bankroll_before = metrics.current_bankroll(str(workspace_root))
    candidate["workspace_root"] = str(workspace_root)
    record = build_record(
        candidate, side, selected_probability, confidence, reasoning, bankroll_before
    )
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
                "selection_source": record["selection_source"],
                "wallets": record["wallets"],
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
        raise ValueError("no staged candidate for today")

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
        "volume": float(candidate.get("volume", 0.0) or 0.0),
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
            "usage: _polymarket_decide.py <workspace_root> SKIP <reasoning> "
            "or _polymarket_decide.py <workspace_root> <side> <probability> <confidence> <reasoning>",
            file=sys.stderr,
        )
        sys.exit(1)

    workspace_root = sys.argv[1]
    mode = sys.argv[2]

    if mode == "SKIP":
        reasoning = (
            " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "No trade selected."
        )
        print(json.dumps(record_explicit_skip(workspace_root, reasoning)))
        return

    if len(sys.argv) < 6:
        print("missing probability/confidence/reasoning", file=sys.stderr)
        sys.exit(1)

    side = mode
    model_probability = sys.argv[3]
    confidence = sys.argv[4]
    reasoning = " ".join(sys.argv[5:])
    print(
        json.dumps(
            evaluate_staged_candidate(
                workspace_root, side, model_probability, confidence, reasoning
            )
        )
    )


if __name__ == "__main__":
    main()

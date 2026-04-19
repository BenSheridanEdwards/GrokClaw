#!/usr/bin/env python3
"""
Feedback-loop ledger for Alpha Polymarket.

Reads existing decisions/results JSONLs and computes:
  - per-wallet win/loss/PnL stats and a Bayesian blend weight
  - per-source recent win-rate and a stake multiplier (kill switch)
  - loss-similarity stake multiplier (token overlap against recent losses)
  - global calibration shrink factor when there are enough resolved trades

This module is read-only — it never mutates persisted data. Callers apply
the multipliers it returns at decision time.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[1]))
RESULTS_FILE = "data/polymarket-results.json"
DECISIONS_FILE = "data/polymarket-decisions.json"

# Wallet blend weight (how much we anchor the model probability to the whale
# vs to the market). Cold start (0W-0L with prior) = ~0.525, near base.
WALLET_WEIGHT_FLOOR = 0.20
WALLET_WEIGHT_CAP = 0.85
WALLET_BETA_PRIOR_WIN = 2.0
WALLET_BETA_PRIOR_LOSS = 2.0

# Source kill switch
SOURCE_WINDOW = 10
SOURCE_MIN_SAMPLES = 3
SOURCE_KILL_THRESHOLD = 0.40
SOURCE_KILL_MULTIPLIER = 0.5

# Calibration shrink (move blended prob toward market when historically miscalibrated)
CALIBRATION_MIN_SAMPLES = 20
CALIBRATION_BAD_THRESHOLD = 0.15  # >15pp avg miscalibration
CALIBRATION_MULTIPLIER = 0.80

# Loss similarity
SIMILARITY_OVERLAP_THRESHOLD = 3
SIMILARITY_LOSS_COUNT = 2
SIMILARITY_STAKE_MULTIPLIER = 0.5


def _resolve_path(workspace_root, relative):
    base = Path(workspace_root) if workspace_root else WORKSPACE_ROOT
    return base / relative


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def load_results(workspace_root=None) -> list[dict]:
    return _load_jsonl(_resolve_path(workspace_root, RESULTS_FILE))


def load_decisions(workspace_root=None) -> list[dict]:
    return _load_jsonl(_resolve_path(workspace_root, DECISIONS_FILE))


def token_set(text: str) -> set:
    if not text:
        return set()
    return {tok for tok in "".join(c.lower() if c.isalnum() else " " for c in text).split() if tok}


def _decision_source_index(workspace_root=None) -> dict:
    out = {}
    for d in load_decisions(workspace_root):
        mid = str(d.get("market_id"))
        src = d.get("selection_source")
        if src and mid not in out:
            out[mid] = src
    return out


def _result_source(result: dict, source_index: dict) -> str:
    return result.get("selection_source") or source_index.get(str(result.get("market_id"))) or ""


def _result_wallets(result: dict) -> list:
    raw = result.get("wallets") or []
    return [str(w).lower() for w in raw if w]


def wallet_stats(wallet: str, workspace_root=None, exclude_market_id=None) -> dict:
    wallet = wallet.lower()
    wins = losses = 0
    pnl = 0.0
    for r in load_results(workspace_root):
        if exclude_market_id and str(r.get("market_id")) == str(exclude_market_id):
            continue
        if r.get("won") is None:
            continue
        if wallet not in _result_wallets(r):
            continue
        if r["won"]:
            wins += 1
        else:
            losses += 1
        pnl += float(r.get("pnl_amount") or 0)
    return {"wallet": wallet, "wins": wins, "losses": losses, "pnl": round(pnl, 2)}


def wallet_blend_weight(wallet: str, workspace_root=None, exclude_market_id=None) -> float:
    s = wallet_stats(wallet, workspace_root=workspace_root, exclude_market_id=exclude_market_id)
    posterior = (WALLET_BETA_PRIOR_WIN + s["wins"]) / (
        WALLET_BETA_PRIOR_WIN + WALLET_BETA_PRIOR_LOSS + s["wins"] + s["losses"]
    )
    weight = WALLET_WEIGHT_FLOOR + (WALLET_WEIGHT_CAP - WALLET_WEIGHT_FLOOR) * posterior
    return round(max(WALLET_WEIGHT_FLOOR, min(WALLET_WEIGHT_CAP, weight)), 4)


def source_stats(source: str, workspace_root=None, window=SOURCE_WINDOW, exclude_market_id=None) -> dict:
    if not source:
        return {"source": source, "samples": 0, "wins": 0, "losses": 0, "win_rate": None, "pnl": 0.0}
    idx = _decision_source_index(workspace_root)
    matching = []
    for r in load_results(workspace_root):
        if exclude_market_id and str(r.get("market_id")) == str(exclude_market_id):
            continue
        if r.get("won") is None:
            continue
        if _result_source(r, idx) == source:
            matching.append(r)
    matching = matching[-window:]
    wins = sum(1 for r in matching if r["won"])
    losses = len(matching) - wins
    win_rate = (wins / len(matching)) if matching else None
    pnl = round(sum(float(r.get("pnl_amount") or 0) for r in matching), 2)
    return {
        "source": source,
        "samples": len(matching),
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 4) if win_rate is not None else None,
        "pnl": pnl,
    }


def source_stake_multiplier(source: str, workspace_root=None) -> float:
    s = source_stats(source, workspace_root=workspace_root)
    if s["samples"] < SOURCE_MIN_SAMPLES:
        return 1.0
    if s["win_rate"] is not None and s["win_rate"] < SOURCE_KILL_THRESHOLD:
        return SOURCE_KILL_MULTIPLIER
    return 1.0


def similar_recent_losses(question: str, source: str, workspace_root=None) -> list[dict]:
    if not question or not source:
        return []
    idx = _decision_source_index(workspace_root)
    q_tokens = token_set(question)
    out = []
    for r in load_results(workspace_root):
        if r.get("won") is True or r.get("won") is None:
            continue
        if _result_source(r, idx) != source:
            continue
        overlap = len(q_tokens & token_set(r.get("question", "")))
        if overlap >= SIMILARITY_OVERLAP_THRESHOLD:
            out.append(r)
    return out


def similarity_stake_multiplier(question: str, source: str, workspace_root=None) -> float:
    losses = similar_recent_losses(question, source, workspace_root=workspace_root)
    if len(losses) >= SIMILARITY_LOSS_COUNT:
        return SIMILARITY_STAKE_MULTIPLIER
    return 1.0


def calibration_multiplier(workspace_root=None) -> tuple:
    """Return (multiplier, info_dict). Multiplier shrinks (blended - market) toward 0
    when historical predictions are systematically miscalibrated.
    """
    results = []
    for r in load_results(workspace_root):
        if r.get("won") is None:
            continue
        # Probability we assigned to OUR side at decision time
        side = r.get("side")
        prob_yes = r.get("probability_yes")
        if prob_yes is None:
            prob_yes = r.get("model_probability")
        if prob_yes is None:
            continue
        try:
            p = float(prob_yes) if side == "YES" else (1.0 - float(prob_yes))
        except (TypeError, ValueError):
            continue
        results.append((p, bool(r["won"])))
    if len(results) < CALIBRATION_MIN_SAMPLES:
        return 1.0, {"samples": len(results), "applied": False, "reason": "insufficient_samples"}

    buckets = defaultdict(lambda: {"wins": 0, "total": 0, "predicted_sum": 0.0})
    for p, won in results:
        bucket = round(p / 0.05) * 0.05
        buckets[bucket]["total"] += 1
        buckets[bucket]["predicted_sum"] += p
        if won:
            buckets[bucket]["wins"] += 1
    weighted_error = 0.0
    total = 0
    for stats in buckets.values():
        actual = stats["wins"] / stats["total"]
        predicted = stats["predicted_sum"] / stats["total"]
        weighted_error += stats["total"] * abs(actual - predicted)
        total += stats["total"]
    avg_error = weighted_error / total if total else 0.0
    if avg_error > CALIBRATION_BAD_THRESHOLD:
        return CALIBRATION_MULTIPLIER, {
            "samples": total,
            "applied": True,
            "avg_error": round(avg_error, 4),
        }
    return 1.0, {
        "samples": total,
        "applied": False,
        "avg_error": round(avg_error, 4),
    }


def topic_source_calibration(question, source, workspace_root=None):
    """Return (samples, brier) for resolved predictions in the same topic × source.

    Pulls the topic cluster from _polymarket_topics and counts all resolved
    results whose question falls in the same cluster and was selected via the
    same source. Used as a predict-only calibration gate: no stakes should be
    placed on a (topic, source) combo with too few samples or a bad Brier.
    """
    from tools import _polymarket_topics as topics_mod

    target_cluster = topics_mod.classify_question(question)
    if not target_cluster:
        return 0, None

    results = load_results(workspace_root)
    source_index = _decision_source_index(workspace_root)
    errors = []
    for r in results:
        r_src = _result_source(r, source_index)
        if r_src != source:
            continue
        r_cluster = topics_mod.classify_question(r.get("question"))
        if r_cluster != target_cluster:
            continue
        prob_yes = r.get("probability_yes")
        if prob_yes is None:
            continue
        outcome = 1.0 if r.get("winning_side") == "YES" else 0.0
        errors.append((float(prob_yes) - outcome) ** 2)

    if not errors:
        return 0, None
    return len(errors), sum(errors) / len(errors)


def short_wallet(wallet: str, prefix: int = 6) -> str:
    if not wallet:
        return ""
    w = str(wallet)
    if len(w) <= prefix + 3:
        return w
    return f"{w[:prefix]}…"

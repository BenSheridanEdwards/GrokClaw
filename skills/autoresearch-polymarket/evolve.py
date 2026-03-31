#!/usr/bin/env python3
"""
Evolve discovery weights via simple walk-forward on resolved binary markets.
Stdlib only. Safe: read Polymarket JSON + write strategy JSON under data/.

Usage:
  python3 skills/autoresearch-polymarket/evolve.py [--dry] [--max-markets N]

Prints a line: EVOLVED_TELEGRAM: Evolved discovery: +X.X% backtest on Y markets (holdout ...)
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any

# Repo root is two levels up from this file
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HERE))
_STRATEGY_PATH = os.path.join(_REPO_ROOT, "data", "autoresearch-polymarket-strategy.json")
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from discovery import (  # noqa: E402
    StrategyWeights,
    baseline_side,
    binary_yes_no_market,
    iter_market_pages,
    market_matches_discovery_filters,
    pick_side_evolved,
    score_market,
    winning_label,
)


def load_strategy() -> StrategyWeights:
    if not os.path.isfile(_STRATEGY_PATH):
        return StrategyWeights()
    try:
        with open(_STRATEGY_PATH, encoding="utf-8") as fh:
            d = json.load(fh)
        params = d.get("weights") if isinstance(d, dict) else None
        if isinstance(params, dict):
            return StrategyWeights.from_dict(params)
    except (OSError, json.JSONDecodeError, TypeError, KeyError):
        pass
    return StrategyWeights()


def sim_roi(win: int, total: int) -> float:
    """Per-market edge vs fair 50c entry: 100 * (2 * p - 1)."""
    if total <= 0:
        return 0.0
    p = win / total
    return 100.0 * (2.0 * p - 1.0)


def collect_resolved_markets(
    max_markets: int,
    page_size: int = 80,
    require_category: bool = True,
) -> list[dict[str, Any]]:
    markets: list[dict[str, Any]] = []
    seen: set[str] = set()
    for batch in iter_market_pages(
        active=True,
        closed=True,
        page_size=page_size,
        max_pages=30,
        order="volume",
        ascending=False,
    ):
        for m in batch:
            if not binary_yes_no_market(m):
                continue
            if require_category and not market_matches_discovery_filters(m):
                continue
            wl = winning_label(m)
            if wl is None:
                continue
            cid = str(m.get("conditionId") or m.get("id") or "").lower()
            if not cid or cid in seen:
                continue
            seen.add(cid)
            markets.append(m)
            if len(markets) >= max_markets:
                return markets
    return markets


def _batch_score_median(
    markets: list[dict[str, Any]],
    weights: StrategyWeights,
) -> float:
    if not markets:
        return 0.0
    vals = sorted(score_market(m, weights) for m in markets)
    return vals[len(vals) // 2]


def evaluate_weights(
    markets: list[dict[str, Any]],
    weights: StrategyWeights,
) -> tuple[int, int, int, int]:
    """Returns evolved_wins, evolved_n, baseline_wins, baseline_n."""
    med = _batch_score_median(markets, weights)
    ev_w = ev_n = bs_w = bs_n = 0
    for m in markets:
        truth = winning_label(m)
        if truth is None:
            continue
        ps = pick_side_evolved(m, weights, score_median=med)
        if ps is None:
            continue
        ev_n += 1
        if ps == truth:
            ev_w += 1
        b = baseline_side(m)
        bs_n += 1
        if b == truth:
            bs_w += 1
    return ev_w, ev_n, bs_w, bs_n


def grid_mutate(base: StrategyWeights, rng: random.Random) -> StrategyWeights:
    return StrategyWeights(
        w_volume=base.w_volume * rng.choice([0.85, 1.0, 1.15]),
        w_liquidity=max(0.0, base.w_liquidity * rng.choice([0.7, 1.0, 1.3])),
        w_days_to_end=base.w_days_to_end * rng.choice([0.8, 1.0, 1.2]),
        w_category=base.w_category * rng.choice([0.85, 1.0, 1.15]),
        side_threshold=base.side_threshold + rng.choice([-0.05, 0.0, 0.05]),
        version=base.version + 1,
    )


def evolve(
    markets: list[dict[str, Any]],
    *,
    base: StrategyWeights,
    iterations: int = 24,
    seed: int = 42,
) -> tuple[StrategyWeights, float, float]:
    rng = random.Random(seed)
    if len(markets) < 20:
        ev_w, ev_n, bs_w, bs_n = evaluate_weights(markets, base)
        return base, sim_roi(ev_w, ev_n), sim_roi(bs_w, bs_n)

    cut = max(int(len(markets) * 0.75), len(markets) - 5)
    train = markets[:cut]
    test = markets[cut:]

    best = base
    best_roi = sim_roi(*evaluate_weights(train, best)[:2])

    for _ in range(iterations):
        cand = grid_mutate(best, rng)
        w, n, _, _ = evaluate_weights(train, cand)
        roi = sim_roi(w, n)
        if roi > best_roi:
            best_roi = roi
            best = cand

    ev_w, ev_n, bs_w, bs_n = evaluate_weights(test, best)
    return best, sim_roi(ev_w, ev_n), sim_roi(bs_w, bs_n)


def main() -> int:
    ap = argparse.ArgumentParser(description="Evolve Polymarket discovery weights")
    ap.add_argument("--dry", action="store_true", help="Do not write strategy JSON")
    ap.add_argument("--max-markets", type=int, default=120, help="Max resolved markets")
    ap.add_argument("--iterations", type=int, default=28)
    args = ap.parse_args()

    base = load_strategy()
    markets = collect_resolved_markets(args.max_markets, require_category=True)
    if len(markets) < 30:
        markets = collect_resolved_markets(
            args.max_markets, require_category=False
        )
    if len(markets) < 8:
        print(
            "EVOLVED_TELEGRAM: Evolved discovery: +0.0% backtest on 0 markets (insufficient API data)",
            file=sys.stderr,
        )
        print("markets_collected=", len(markets))
        return 1

    new_w, roi_ev, roi_bs = evolve(
        markets,
        base=base,
        iterations=args.iterations,
    )
    uplift = roi_ev - roi_bs
    n = len(markets)
    summary = (
        f"Evolved discovery: {uplift:+.1f}% backtest on {n} markets "
        f"(holdout {roi_ev:+.1f}% vs baseline {roi_bs:+.1f}%)"
    )
    print(f"EVOLVED_TELEGRAM: {summary}")
    print(
        json.dumps(
            {
                "weights": new_w.to_dict(),
                "metrics": {
                    "resolved_markets": n,
                    "sim_roi_evolved_pct": round(roi_ev, 2),
                    "sim_roi_baseline_pct": round(roi_bs, 2),
                    "uplift_pct": round(uplift, 2),
                },
                "notes": "Sim ROI assumes 50c entry vs 0/1 resolution; exploratory metric only.",
            },
            indent=2,
        )
    )

    if not args.dry:
        os.makedirs(os.path.dirname(_STRATEGY_PATH), exist_ok=True)
        payload = {
            "weights": new_w.to_dict(),
            "metrics": {
                "resolved_markets": n,
                "sim_roi_evolved_pct": round(roi_ev, 2),
                "sim_roi_baseline_pct": round(roi_bs, 2),
                "uplift_pct": round(uplift, 2),
            },
        }
        with open(_STRATEGY_PATH, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

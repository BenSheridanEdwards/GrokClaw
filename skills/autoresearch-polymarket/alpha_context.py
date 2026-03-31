#!/usr/bin/env python3
"""Print discovery context for Alpha (stdout). Stdlib only."""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HERE))
_STRATEGY_PATH = os.path.join(_REPO_ROOT, "data", "autoresearch-polymarket-strategy.json")
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from discovery import StrategyWeights, discover_candidates  # noqa: E402


def main() -> int:
    weights = StrategyWeights()
    if os.path.isfile(_STRATEGY_PATH):
        try:
            with open(_STRATEGY_PATH, encoding="utf-8") as fh:
                d = json.load(fh)
            p = d.get("weights")
            if isinstance(p, dict):
                weights = StrategyWeights.from_dict(p)
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    rows = discover_candidates(
        active=True,
        closed=False,
        page_size=50,
        max_pages=6,
        top_n=15,
        weights=weights,
        require_category=True,
    )
    met = {}
    if os.path.isfile(_STRATEGY_PATH):
        try:
            with open(_STRATEGY_PATH, encoding="utf-8") as fh:
                blob = json.load(fh)
            met = blob.get("metrics") if isinstance(blob.get("metrics"), dict) else {}
        except (OSError, json.JSONDecodeError):
            pass

    print("## Polymarket discovery (evolved strategy)", file=sys.stdout)
    if met:
        print(
            f"- Last evolve: uplift ~{met.get('uplift_pct', '?')}% sim vs baseline, "
            f"n={met.get('resolved_markets', '?')} resolved (see evolve.py)",
            file=sys.stdout,
        )
    print(f"- Strategy version: w_vol={weights.w_volume:.3f} threshold={weights.side_threshold:.3f}", file=sys.stdout)
    print("- Top candidates (score / side_hint / volume / question):", file=sys.stdout)
    for r in rows[:10]:
        q = (r.get("question") or "")[:100]
        print(
            f"  * {r.get('score')} {r.get('side_hint')} vol={r.get('volume')} :: {q}",
            file=sys.stdout,
        )
    print(
        "\nUse web_search for cross-checks (e.g. sports/politics lines vs Pinnacle where applicable).",
        file=sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

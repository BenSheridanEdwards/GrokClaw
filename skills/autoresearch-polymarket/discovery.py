#!/usr/bin/env python3
"""
Polymarket multi-page discovery — stdlib only, HTTPS read to gamma-api only.
Inspired by AutoResearchClaw-style evolution hooks (observe → score → refine).

Fetches paginated markets, scores them for paper-trading style discovery,
and exports structured candidates. No subprocess / no extra pip deps.
"""
from __future__ import annotations

import json
import math
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterator

GAMMA_MARKETS = "https://gamma-api.polymarket.com/markets"
DEFAULT_UA = "GrokClaw-autoresearch-polymarket/1.0"

# Binary YES/NO — same keyword universe as _polymarket_trade (partial overlap)
CRYPTO_KEYWORDS = (
    "bitcoin", "btc", "ethereum", "crypto", "solana", "defi",
    "blockchain", "etf", "halving", "mining", "sec",
)
GEOPOLITICAL_KEYWORDS = (
    "russia", "ukraine", "china", "iran", "israel", "election", "trump", "biden",
    "congress", "senate", "fed", "rate cut", "inflation", "ceasefire", "war",
    "sanctions", "nato", "tariff", "geopol", "putin", "taiwan", "gaza",
)


@dataclass
class StrategyWeights:
    """Evolved linear scoring weights (updated by evolve.py)."""

    w_volume: float = 1.0
    w_liquidity: float = 0.25
    w_days_to_end: float = -0.02
    w_category: float = 0.35
    side_threshold: float = 0.0
    version: int = 1

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StrategyWeights:
        return cls(
            w_volume=float(d.get("w_volume", 1.0)),
            w_liquidity=float(d.get("w_liquidity", 0.25)),
            w_days_to_end=float(d.get("w_days_to_end", -0.02)),
            w_category=float(d.get("w_category", 0.35)),
            side_threshold=float(d.get("side_threshold", 0.0)),
            version=int(d.get("version", 1)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def fetch_json(url: str, timeout: int = 45) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def iter_market_pages(
    *,
    active: bool = True,
    closed: bool = False,
    page_size: int = 50,
    max_pages: int,
    order: str = "volume",
    ascending: bool = False,
    extra: dict[str, str] | None = None,
) -> Iterator[list[dict[str, Any]]]:
    extra = extra or {}
    for page in range(max_pages):
        offset = page * page_size
        q: dict[str, str] = {
            "active": str(active).lower(),
            "closed": str(closed).lower(),
            "limit": str(page_size),
            "offset": str(offset),
            "order": order,
            "ascending": str(ascending).lower(),
        }
        q.update(extra)
        url = f"{GAMMA_MARKETS}?{urllib.parse.urlencode(q)}"
        batch = fetch_json(url)
        if not isinstance(batch, list) or not batch:
            break
        yield batch
        if len(batch) < page_size:
            break


def market_matches_discovery_filters(market: dict[str, Any]) -> bool:
    text = " ".join(
        str(market.get(k, "")) for k in ("question", "description", "groupItemTitle")
    ).lower()
    keywords = CRYPTO_KEYWORDS + GEOPOLITICAL_KEYWORDS
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", text):
            return True
    return False


def parse_json_list_field(raw: Any) -> list[Any]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            val = json.loads(raw)
            return val if isinstance(val, list) else []
        except json.JSONDecodeError:
            return []
    return []


def binary_yes_no_market(market: dict[str, Any]) -> bool:
    outs = parse_json_list_field(market.get("outcomes"))
    if len(outs) != 2:
        return False
    labels = [str(o).strip().lower() for o in outs]
    norm = {re.sub(r"[^a-z]", "", x) for x in labels}
    return norm == {"yes", "no"}


def float_field(m: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for k in keys:
        raw = m.get(k)
        if raw is None:
            continue
        try:
            v = float(raw)
            if math.isfinite(v):
                return v
        except (TypeError, ValueError):
            continue
    return default


def days_until_end(market: dict[str, Any]) -> float | None:
    end_str = market.get("endDate") or market.get("end_date_iso")
    if not end_str:
        return None
    try:
        end = datetime.fromisoformat(str(end_str).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    now = datetime.now(timezone.utc)
    delta = end - now
    return max(delta.total_seconds() / 86400.0, 0.0)


def volume_score(market: dict[str, Any]) -> float:
    v = float_field(market, "volumeNum", "volume")
    return math.log1p(max(v, 0.0))


def liquidity_proxy(market: dict[str, Any]) -> float:
    """Use CLOB volume as liquidity proxy when present."""
    return float_field(market, "volumeClob", "volumeNum", "volume")


def score_market(
    market: dict[str, Any],
    weights: StrategyWeights,
) -> float:
    d_end = days_until_end(market)
    days_term = d_end if d_end is not None else 30.0
    cat = 1.0 if market_matches_discovery_filters(market) else 0.0
    return (
        weights.w_volume * volume_score(market)
        + weights.w_liquidity * math.log1p(max(liquidity_proxy(market), 0.0))
        + weights.w_days_to_end * days_term
        + weights.w_category * cat
    )


def pick_side_evolved(
    market: dict[str, Any],
    weights: StrategyWeights,
    score_median: float | None = None,
) -> str | None:
    """YES if score is above batch median + threshold; else NO (learnable vs always-YES)."""
    s = score_market(market, weights)
    if score_median is None:
        return "YES" if s >= weights.side_threshold else "NO"
    return "YES" if s >= score_median + weights.side_threshold else "NO"


def parse_outcome_prices(market: dict[str, Any]) -> tuple[list[str], list[float]]:
    labels = [str(x) for x in parse_json_list_field(market.get("outcomes"))]
    prices_raw = parse_json_list_field(market.get("outcomePrices"))
    prices: list[float] = []
    for p in prices_raw:
        try:
            prices.append(float(p))
        except (TypeError, ValueError):
            prices.append(0.0)
    return labels, prices


def winning_label(market: dict[str, Any]) -> str | None:
    """For a resolved binary market, return normalized YES/NO winning side."""
    if not binary_yes_no_market(market):
        return None
    labels, prices = parse_outcome_prices(market)
    if len(labels) < 2 or len(prices) < 2:
        return None
    winners = [i for i, p in enumerate(prices) if p >= 0.999]
    if len(winners) != 1:
        return None
    w = re.sub(r"[^a-z]", "", str(labels[winners[0]]).strip().lower())
    if w == "yes":
        return "YES"
    if w == "no":
        return "NO"
    return None


def baseline_side(_market: dict[str, Any]) -> str:
    """Dumb baseline: always YES (matches naive long-bias tests)."""
    return "YES"


def discover_candidates(
    *,
    active: bool = True,
    closed: bool = False,
    page_size: int = 50,
    max_pages: int = 5,
    top_n: int = 60,
    weights: StrategyWeights | None = None,
    require_category: bool = True,
) -> list[dict[str, Any]]:
    weights = weights or StrategyWeights()
    scored: list[tuple[float, dict[str, Any]]] = []
    seen: set[str] = set()
    for batch in iter_market_pages(
        active=active,
        closed=closed,
        page_size=page_size,
        max_pages=max_pages,
    ):
        for m in batch:
            if not binary_yes_no_market(m):
                continue
            if require_category and not market_matches_discovery_filters(m):
                continue
            cid = str(m.get("conditionId") or m.get("id") or "").lower()
            if cid in seen:
                continue
            seen.add(cid)
            s = score_market(m, weights)
            scored.append((s, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    median_s = scored[len(scored) // 2][0] if scored else 0.0
    for s, m in scored[:top_n]:
        d_end = days_until_end(m)
        out.append(
            {
                "score": round(s, 4),
                "condition_id": m.get("conditionId"),
                "id": m.get("id"),
                "question": m.get("question"),
                "volume": float_field(m, "volumeNum", "volume"),
                "days_to_end": round(d_end, 2) if d_end is not None else None,
                "side_hint": pick_side_evolved(m, weights, score_median=median_s),
            }
        )
    return out

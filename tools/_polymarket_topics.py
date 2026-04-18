#!/usr/bin/env python3
"""Topic clustering for Polymarket questions.

A deliberately coarse keyword classifier used to detect when the paper book
is over-concentrated in one theme. The goal is not a perfect taxonomy — it
is to stop the situation that produced trades 1-5 (five Iran/US geopolitical
bets opened in four days) where a single news cycle can take down the whole
book.

Clusters are matched on normalized question text by keyword membership. The
first cluster with a matching keyword wins; ordering of the dict below is
intentional — more specific clusters come before more generic ones.

Stdlib only.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, Optional

TOPIC_CLUSTERS: "dict[str, set[str]]" = {
    "iran_us": {
        "iran", "iranian", "hormuz", "tehran", "uranium", "enriched",
        "ayatollah", "strait of hormuz",
    },
    "israel": {
        "israel", "israeli", "gaza", "hamas", "hezbollah", "lebanon",
        "idf", "netanyahu",
    },
    "russia_ukraine": {
        "russia", "russian", "ukraine", "ukrainian", "putin", "zelensky",
        "kyiv", "moscow", "kremlin",
    },
    "china_taiwan": {
        "china", "chinese", "taiwan", "taiwanese", "xi jinping", "beijing",
        "tpe",
    },
    "korea": {"north korea", "kim jong", "pyongyang", "dprk"},
    "btc_crypto": {
        "bitcoin", "btc", "ethereum", "eth", "solana", " sol ",
        "crypto", "stablecoin", "usdt", "usdc",
    },
    "us_politics_trump": {
        "trump", "maga", "white house",
    },
    "us_politics_biden": {"biden", "harris"},
    "election": {
        "election", "primary", "caucus", "electoral", "ballot",
    },
    "ai_tech": {
        "openai", "anthropic", "claude", "gpt", "nvidia", "semiconductor",
        "tsmc", "gemini", "llama", "mistral",
    },
    "climate_weather": {
        "hurricane", "typhoon", "heatwave", "temperature record",
        "el niño", "el nino", "climate",
    },
    "sports": {
        "nba", "nfl", "mlb", "super bowl", "world cup", "premier league",
        "champions league", "olympic",
    },
}


def _normalize(text: str) -> str:
    # Lowercase, pad with spaces so whole-word checks like " sol " work.
    return " " + re.sub(r"\s+", " ", text.lower()) + " "


def classify_question(question: Optional[str]) -> Optional[str]:
    if not question:
        return None
    haystack = _normalize(question)
    for cluster, keywords in TOPIC_CLUSTERS.items():
        for kw in keywords:
            needle = kw if " " in kw else f" {kw} "
            if needle in haystack:
                return cluster
            # Also match keyword as a prefix bounded by non-letter (handles
            # "Iran-US", "Iran's", "Iran:" without padding every keyword).
            if re.search(rf"\b{re.escape(kw)}\b", haystack):
                return cluster
    return None


def open_clusters_from_ledger(
    trades: Iterable[dict],
    results: Iterable[dict],
) -> "dict[str, int]":
    """Count open (unresolved) trades per topic cluster.

    trades: iterable of trade records (with market_id + question).
    results: iterable of resolution records (with market_id).
    """
    resolved = {str((r.get("market_id") or "")).lower() for r in results}
    counts: Counter = Counter()
    for trade in trades:
        mid = str((trade.get("market_id") or "")).lower()
        if not mid or mid in resolved:
            continue
        cluster = classify_question(trade.get("question"))
        if cluster:
            counts[cluster] += 1
    return dict(counts)

#!/usr/bin/env python3
"""
Sentient prediction market paper trade: fetch model-arena markets (Grok vs Claude), stage candidate.
Uses Manifold API (api.manifold.markets) for market data. Paper trading only.
Stdlib only. Called from sentient-trade.sh.
"""
import json
import math
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from tools import _sentient_metrics as metrics

API_BASE = "https://api.manifold.markets"
TRADES_FILE = "data/sentient-trades.json"
PENDING_FILE = "data/sentient-pending-trade.json"
DECISIONS_FILE = "data/sentient-decisions.json"

MODEL_ARENA_KEYWORDS = (
    "grok", "claude", "gemini", "gpt", "model arena", "lmarena", "vs ",
    "chatbot", "llm", "ai model", "anthropic", "openai", "xai", "google",
)


def get_already_evaluated_ids(workspace_root, days=2):
    """Return set of market IDs we've already decided/traded in last N days."""
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    excluded = set()
    for path in [
        os.path.join(workspace_root, DECISIONS_FILE),
        os.path.join(workspace_root, TRADES_FILE),
    ]:
        for row in metrics.load_jsonl(path):
            if (row.get("date") or "") < cutoff:
                continue
            mid = row.get("market_id")
            if mid:
                excluded.add(str(mid).lower())
    return excluded


def market_matches_model_arena(market):
    """True if market question matches model-arena themes (Grok vs Claude, etc.)."""
    text = " ".join(
        str(market.get(k, "")) for k in ("question", "description", "textDescription")
    ).lower()
    for kw in MODEL_ARENA_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", text):
            return True
    return False


def fetch_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "GrokClaw-Sentient/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def search_markets(term="", limit=50):
    params = urllib.parse.urlencode({
        "term": term,
        "limit": str(limit),
        "filter": "open",
        "contractType": "BINARY",
        "sort": "liquidity",
    })
    url = f"{API_BASE}/v0/search-markets?{params}"
    try:
        return fetch_json(url)
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
        return []


def select_market(markets, excluded_ids=None):
    """Select best model-arena market: binary, open, closing within 14 days, sufficient liquidity."""
    excluded_ids = excluded_ids or set()
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=14)
    best = None
    best_score = 0.0

    for m in markets:
        if not market_matches_model_arena(m):
            continue
        mid = str(m.get("id") or "").lower()
        if not mid or mid in excluded_ids:
            continue
        if m.get("isResolved"):
            continue
        close_ms = m.get("closeTime")
        if not close_ms:
            continue
        try:
            close_dt = datetime.fromtimestamp(close_ms / 1000, tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            continue
        if now >= close_dt or close_dt > cutoff:
            continue
        vol = float(m.get("volume") or 0)
        liq = float(m.get("totalLiquidity") or m.get("pool") or 0)
        if isinstance(liq, dict):
            liq = sum(float(v) for v in liq.values()) if liq else 0
        score = (vol * 0.3) + (liq * 0.7)
        if score > best_score:
            best_score = score
            best = m

    return best


def validate_odds(odds):
    value = float(odds)
    if not math.isfinite(value) or value <= 0 or value > 1:
        raise ValueError("odds must be a finite float in (0, 1]")
    return value


def log_trade(workspace_root, market_id, question, side, odds, reasoning, metadata=None):
    trades_path = os.path.join(workspace_root, TRADES_FILE)
    os.makedirs(os.path.dirname(trades_path), exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    normalized_odds = validate_odds(odds)
    entry = {
        "date": today,
        "market_id": market_id,
        "question": question,
        "side": side,
        "odds": normalized_odds,
        "reasoning": reasoning,
        "resolved": False,
    }
    if metadata:
        entry.update(metadata)
    line = json.dumps(entry) + "\n"
    with open(trades_path, "a") as f:
        f.write(line)
    print(f"Logged trade: {question[:50]}... ({side} @ {odds})")


def stage_candidate(workspace_root, candidate):
    pending_path = os.path.join(workspace_root, PENDING_FILE)
    os.makedirs(os.path.dirname(pending_path), exist_ok=True)
    with open(pending_path, "w", encoding="utf-8") as handle:
        json.dump(candidate, handle)


def load_staged_candidate(workspace_root):
    pending_path = os.path.join(workspace_root, PENDING_FILE)
    if not os.path.exists(pending_path):
        return None
    with open(pending_path, encoding="utf-8") as handle:
        return json.load(handle)


def clear_staged_candidate(workspace_root):
    pending_path = os.path.join(workspace_root, PENDING_FILE)
    if os.path.exists(pending_path):
        os.remove(pending_path)


def log_staged_trade(workspace_root, side, reasoning):
    candidate = load_staged_candidate(workspace_root)
    if candidate is None:
        raise ValueError("no staged candidate")

    odds_key = "odds_yes" if side == "YES" else "odds_no"
    log_trade(
        str(workspace_root),
        candidate["market_id"],
        candidate["question"],
        side,
        candidate[odds_key],
        reasoning,
    )
    clear_staged_candidate(workspace_root)


def main():
    if len(sys.argv) <= 2:
        workspace_root = sys.argv[1] if len(sys.argv) >= 2 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        excluded_ids = get_already_evaluated_ids(workspace_root, days=2)
        markets = search_markets(term="grok", limit=100)
        if not markets or len(markets) < 5:
            markets = search_markets(term="claude", limit=100)
        if not markets:
            markets = search_markets(term="model arena", limit=100)
        if not markets:
            markets = search_markets(limit=200)

        best = select_market(markets, excluded_ids=excluded_ids)
        if not best:
            print(
                "No suitable model-arena market found (Grok vs Claude, binary, open, closing within 14 days).",
                file=sys.stderr,
            )
            sys.exit(1)

        prob = float(best.get("probability", 0.5))
        odds_yes = prob
        odds_no = 1.0 - odds_yes

        out = {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "id": best.get("id"),
            "market_id": best.get("id"),
            "question": best.get("question", ""),
            "odds_yes": odds_yes,
            "odds_no": odds_no,
            "volume": best.get("volume"),
            "closeTime": best.get("closeTime"),
            "url": best.get("url"),
        }
        stage_candidate(workspace_root, out)
        print(json.dumps(out))
        return

    if len(sys.argv) == 4:
        workspace_root = sys.argv[1]
        side = sys.argv[2]
        reasoning = sys.argv[3]
        if side not in ("YES", "NO"):
            print("side must be YES or NO", file=sys.stderr)
            sys.exit(1)
        log_staged_trade(workspace_root, side, reasoning)
        return

    print(
        "usage: fetch mode: [workspace_root], or staged log: workspace_root side reasoning",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()

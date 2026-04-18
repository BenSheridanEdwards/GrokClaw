#!/usr/bin/env python3
"""
Polymarket paper trade: fetch markets, select best, or log a trade.
Stdlib only. Called from polymarket-trade.sh.
"""
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from tools import _polymarket_metrics as metrics

API_URL = "https://gamma-api.polymarket.com/markets"
DATA_API_URL = "https://data-api.polymarket.com"
TRADES_FILE = "data/polymarket-trades.json"
PENDING_FILE = "data/polymarket-pending-trade.json"
DECISIONS_FILE = "data/polymarket-decisions.json"
MARKET_PAGE_SIZE = 50
MARKET_MAX_PAGES = 10
LEADERBOARD_LIMIT = 10  # Wider whale net once we filter for matching positions
POSITIONS_PAGE_SIZE = 100
# Widened from 36h → 96h: the 36h window almost never matches anything in the
# geopolitical/crypto allowlist, starving the strategy. 4 days still captures
# the bonding pattern (high-conviction wallet sitting on near-resolution price)
# without straying into pure latency-arb territory.
BONDING_MAX_HOURS_TO_RESOLUTION = 96
WHALE_COPY_MAX_DAYS = 90
# Lowered from 0.95 → 0.85: still expresses strong conviction but unblocks the
# late-stage accumulation pattern we actually want to copy.
BONDING_MIN_PRICE = 0.85
BONDING_MAX_PRICE = 1.0
BONDING_MIN_MATCHING_TRADERS = 1
BONDING_TRADER_WALLETS = (
    "0x751a2b86cab503496efd325c8344e10159349ea1",  # Sharky6999
    "0xd1c769317bd15de7768a70d0214cf0bbcc531d2b",  # 033033033
    "0x7072dd52161bae614bec6905846a53c9a3a53413",  # ForesightOracle
)
SHORT_TERM_LATENCY_PATTERNS = (
    "15 minute",
    "15-minute",
    "15m",
    "in the next 15",
)

# Category keywords: only geopolitical and crypto bets
CRYPTO_KEYWORDS = (
    "bitcoin", "btc", "ethereum", "crypto", "solana", "defi",
    "blockchain", "etf", "halving", "mining", "sec approval", "sec etf",
)
GEOPOLITICAL_KEYWORDS = (
    "russia", "ukraine", "china", "iran", "israel", "election", "trump", "biden",
    "congress", "senate", " fed ", "rate cut", "inflation", "ceasefire", "war",
    "sanctions", "nato", "tariff", "trade war", "geopolit", "putin",
    "nuclear", "military", "invasion", "gaza", "taiwan", "hong kong",
)


def get_already_evaluated_ids(workspace_root, days=7):
    """Return set of market_ids we've already TRADED (not merely skipped) in last N days.

    Skipped markets are eligible for re-evaluation as conditions change (price,
    time-to-resolution, new whale positions); only actual paper trades should
    be excluded to avoid duplicating exposure on the same market.
    """
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    excluded = set()
    for row in metrics.load_jsonl(os.path.join(workspace_root, TRADES_FILE)):
        if (row.get("date") or "") < cutoff:
            continue
        mid = row.get("market_id")
        if mid:
            excluded.add(str(mid).lower())
    return excluded


def market_matches_categories(market):
    """True if market question/description matches geopolitical or crypto (word-boundary)."""
    text = " ".join(
        str(market.get(k, "")) for k in ("question", "description", "groupItemTitle")
    ).lower()
    keywords = CRYPTO_KEYWORDS + GEOPOLITICAL_KEYWORDS
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", text):
            return True
    return False


def fetch_markets(page_size=MARKET_PAGE_SIZE, max_pages=MARKET_MAX_PAGES):
    markets = []
    for page_idx in range(max_pages):
        offset = page_idx * page_size
        page = fetch_markets_page(page_size=page_size, offset=offset)
        if not page:
            break
        markets.extend(page)
        if len(page) < page_size:
            break
    return markets


def fetch_markets_page(page_size, offset):
    url = f"{API_URL}?active=true&closed=false&limit={page_size}&offset={offset}&order=volume&ascending=false"
    req = urllib.request.Request(url, headers={"User-Agent": "GrokClaw/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def market_prices(market):
    prices = market.get("outcomePrices") or market.get("prices") or ["0.5", "0.5"]
    if isinstance(prices, str):
        prices = json.loads(prices) if prices.strip().startswith("[") else [prices, "0.5"]
    odds_yes = float(prices[0]) if prices else 0.5
    odds_no = float(prices[1]) if len(prices) > 1 else 1 - odds_yes
    return odds_yes, odds_no


def market_is_short_term_latency_market(market):
    text = " ".join(
        str(market.get(k, "")) for k in ("question", "description", "groupItemTitle")
    ).lower()
    return any(pattern in text for pattern in SHORT_TERM_LATENCY_PATTERNS)


def fetch_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "GrokClaw/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def select_market(markets, excluded_ids=None):
    """Volume fallback: highest-volume geopolitical/crypto market closing within 7 days."""
    excluded_ids = excluded_ids or set()
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=7)
    best = None
    best_volume = 0
    for m in markets:
        if not market_matches_categories(m):
            continue
        if market_is_short_term_latency_market(m):
            continue
        cid = str(m.get("conditionId") or "").lower()
        mid = str(m.get("id") or m.get("conditionId") or "").lower()
        if cid in excluded_ids or mid in excluded_ids:
            continue
        end_str = m.get("endDate") or m.get("end_date_iso")
        if not end_str:
            continue
        try:
            end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue
        if now < end <= cutoff:
            vol = float(m.get("volume") or m.get("volumeNum") or 0)
            if vol > best_volume:
                best_volume = vol
                best = m
    return best


def market_is_within_window(market, now=None, days=7):
    now = now or datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days)
    end_str = market.get("endDate") or market.get("end_date_iso")
    if not end_str:
        return False
    try:
        end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return False
    return now < end <= cutoff


LEADERBOARD_CATEGORIES = ("CRYPTO", "POLITICS")


def fetch_top_traders(limit=LEADERBOARD_LIMIT):
    """Fetch top traders from crypto and politics leaderboards (not OVERALL, which returns sports bettors)."""
    seen_wallets = set()
    combined = []
    for category in LEADERBOARD_CATEGORIES:
        # MONTH (not WEEK) filters out lucky-streak short-term traders and keeps
        # the wallets with sustained edge — what we actually want to copy.
        query = urllib.parse.urlencode(
            {
                "category": category,
                "timePeriod": "MONTH",
                "orderBy": "PNL",
                "limit": str(limit),
                "offset": "0",
            }
        )
        url = f"{DATA_API_URL}/v1/leaderboard?{query}"
        try:
            data = fetch_json(url, timeout=20)
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for trader in data:
            wallet = (trader.get("proxyWallet") or "").lower()
            if wallet and wallet not in seen_wallets:
                seen_wallets.add(wallet)
                combined.append(trader)
    # Re-rank by position in the combined list
    for i, trader in enumerate(combined):
        trader["rank"] = str(i + 1)
    return combined


def fetch_bonding_traders():
    return [
        {"proxyWallet": wallet, "rank": str(index + 1)}
        for index, wallet in enumerate(BONDING_TRADER_WALLETS)
    ]


def fetch_positions_for_user(user, condition_id=None, limit=POSITIONS_PAGE_SIZE):
    params = {
        "user": user,
        "sizeThreshold": "1",
        "limit": str(limit),
        "offset": "0",
        "sortBy": "CURRENT",
        "sortDirection": "DESC",
    }
    if condition_id:
        params["market"] = condition_id
    query = urllib.parse.urlencode(params)
    url = f"{DATA_API_URL}/positions?{query}"
    data = fetch_json(url, timeout=20)
    if isinstance(data, list):
        return data
    return []


def normalize_outcome_label(outcome):
    label = str(outcome or "").strip().lower()
    if label == "yes":
        return "YES"
    if label == "no":
        return "NO"
    return ""


def normalize_title(value):
    return " ".join(str(value or "").strip().lower().split())


def position_notional(position):
    for key in ("currentValue", "initialValue", "totalBought"):
        raw = position.get(key)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if math.isfinite(value) and value > 0:
            return value

    try:
        size = float(position.get("size") or 0.0)
        price = float(position.get("curPrice") or position.get("avgPrice") or 0.0)
    except (TypeError, ValueError):
        return 0.0
    notional = size * price
    if math.isfinite(notional) and notional > 0:
        return notional
    return 0.0


def build_copy_signal(condition_id, question):
    if not condition_id:
        return {"status": "unavailable", "reason": "missing_condition_id"}

    try:
        traders = fetch_top_traders()
    except Exception as exc:
        return {"status": "unavailable", "reason": f"leaderboard_fetch_failed:{type(exc).__name__}"}

    if not traders:
        return {"status": "unavailable", "reason": "no_top_traders"}

    yes_weight = 0.0
    no_weight = 0.0
    matched_wallets = set()
    samples = []

    for trader in traders:
        wallet = trader.get("proxyWallet")
        if not wallet:
            continue
        rank_raw = trader.get("rank") or "1"
        try:
            rank = max(int(rank_raw), 1)
        except (TypeError, ValueError):
            rank = 1
        rank_weight = 1.0 / float(rank)

        try:
            positions = fetch_positions_for_user(wallet, condition_id=condition_id)
            if not positions:
                # Fallback: fetch broader positions, then match by title.
                positions = fetch_positions_for_user(wallet, condition_id=None)
        except Exception:
            continue

        question_norm = normalize_title(question)
        for position in positions:
            pos_condition = str(position.get("conditionId") or "").lower()
            pos_title = normalize_title(position.get("title"))
            if pos_condition != str(condition_id).lower() and pos_title != question_norm:
                continue
            side = normalize_outcome_label(position.get("outcome"))
            if side not in ("YES", "NO"):
                continue
            notional = position_notional(position)
            if notional <= 0:
                continue
            weighted = notional * rank_weight
            if side == "YES":
                yes_weight += weighted
            else:
                no_weight += weighted
            matched_wallets.add(wallet.lower())
            if len(samples) < 5:
                samples.append(
                    {
                        "wallet": wallet,
                        "rank": rank,
                        "side": side,
                        "notional": round(notional, 2),
                    }
                )

    total = yes_weight + no_weight
    if total <= 0:
        return {
            "status": "unavailable",
            "reason": "no_matching_positions",
            "condition_id": condition_id,
            "question": question,
            "top_traders_considered": len(traders),
        }

    probability_yes = yes_weight / total
    consensus_side = "YES" if probability_yes >= 0.5 else "NO"
    confidence = abs(probability_yes - 0.5) * 2.0
    return {
        "status": "ok",
        "source": "polymarket_data_api",
        "condition_id": condition_id,
        "question": question,
        "top_traders_considered": len(traders),
        "traders_with_matching_positions": len(matched_wallets),
        "consensus_side": consensus_side,
        "consensus_probability_yes": round(probability_yes, 4),
        "confidence": round(confidence, 4),
        "yes_weighted_notional": round(yes_weight, 2),
        "no_weighted_notional": round(no_weight, 2),
        "samples": samples,
    }


def aggregate_top_trader_positions(top_traders):
    aggregates = {}
    for trader in top_traders:
        wallet = trader.get("proxyWallet")
        if not wallet:
            continue
        rank_raw = trader.get("rank") or "1"
        try:
            rank = max(int(rank_raw), 1)
        except (TypeError, ValueError):
            rank = 1
        rank_weight = 1.0 / float(rank)

        try:
            positions = fetch_positions_for_user(wallet, condition_id=None)
        except Exception:
            continue

        for position in positions:
            condition_id = str(position.get("conditionId") or "").strip().lower()
            if not condition_id:
                continue
            side = normalize_outcome_label(position.get("outcome"))
            if side not in ("YES", "NO"):
                continue
            notional = position_notional(position)
            if notional <= 0:
                continue

            entry = aggregates.setdefault(
                condition_id,
                {
                    "condition_id": condition_id,
                    "question": position.get("title") or "",
                    "yes_weight": 0.0,
                    "no_weight": 0.0,
                    "traders": set(),
                    "samples": [],
                },
            )
            weighted = notional * rank_weight
            if side == "YES":
                entry["yes_weight"] += weighted
            else:
                entry["no_weight"] += weighted
            entry["traders"].add(wallet.lower())
            if len(entry["samples"]) < 5:
                entry["samples"].append(
                    {
                        "wallet": wallet,
                        "rank": rank,
                        "side": side,
                        "notional": round(notional, 2),
                    }
                )
    return aggregates


def build_signal_from_aggregate(aggregate, top_traders_considered):
    yes_weight = aggregate["yes_weight"]
    no_weight = aggregate["no_weight"]
    total = yes_weight + no_weight
    if total <= 0:
        return None
    probability_yes = yes_weight / total
    confidence = abs(probability_yes - 0.5) * 2.0
    return {
        "status": "ok",
        "source": "polymarket_data_api",
        "condition_id": aggregate["condition_id"],
        "question": aggregate["question"],
        "top_traders_considered": top_traders_considered,
        "traders_with_matching_positions": len(aggregate["traders"]),
        "consensus_side": "YES" if probability_yes >= 0.5 else "NO",
        "consensus_probability_yes": round(probability_yes, 4),
        "confidence": round(confidence, 4),
        "yes_weighted_notional": round(yes_weight, 2),
        "no_weighted_notional": round(no_weight, 2),
        "samples": aggregate["samples"],
    }


def select_copy_candidate(markets, excluded_ids=None):
    """Select best market from whale top traders' positions. Only geopolitical + crypto."""
    excluded_ids = excluded_ids or set()
    try:
        top_traders = fetch_top_traders()
    except Exception:
        return None, None
    if not top_traders:
        return None, None

    aggregates = aggregate_top_trader_positions(top_traders)
    if not aggregates:
        return None, None

    best_market = None
    best_signal = None
    best_score = 0.0

    for market in markets:
        if not market_is_within_window(market, days=WHALE_COPY_MAX_DAYS):
            continue
        if not market_matches_categories(market):
            continue
        if market_is_short_term_latency_market(market):
            continue
        condition_id = str(market.get("conditionId") or "").strip().lower()
        market_id = str(market.get("id") or market.get("conditionId") or "").lower()
        if not condition_id:
            continue
        if condition_id in excluded_ids or market_id in excluded_ids:
            continue
        aggregate = aggregates.get(condition_id)
        if not aggregate:
            continue
        signal = build_signal_from_aggregate(aggregate, len(top_traders))
        if not signal:
            continue
        trader_count = signal["traders_with_matching_positions"]
        if trader_count < 1:
            continue
        # Skip markets the public has already priced at the same extreme as the
        # whale: edge after blending will be near zero and the decide gate
        # blocks them anyway. Filtering here lets us fall through to the next
        # whale candidate instead of returning a guaranteed-skip market.
        odds_yes, odds_no = market_prices(market)
        side_price = odds_yes if signal["consensus_side"] == "YES" else odds_no
        if side_price >= 0.95 or side_price <= 0.05:
            continue
        notional = signal["yes_weighted_notional"] + signal["no_weighted_notional"]
        score = notional * (0.5 + signal["confidence"])
        if score > best_score:
            best_score = score
            best_market = market
            best_signal = signal

    return best_market, best_signal


def select_bonding_copy_candidate(markets, excluded_ids=None):
    """Copy late-stage high-probability positions from known bonding wallets."""
    excluded_ids = excluded_ids or set()
    traders = fetch_bonding_traders()
    if not traders:
        return None, None
    aggregates = aggregate_top_trader_positions(traders)
    if not aggregates:
        return None, None

    now = datetime.now(timezone.utc)
    bonding_cutoff = now + timedelta(hours=BONDING_MAX_HOURS_TO_RESOLUTION)
    best_market = None
    best_signal = None
    best_score = 0.0

    for market in markets:
        if not market_matches_categories(market):
            continue
        if market_is_short_term_latency_market(market):
            continue
        end_str = market.get("endDate") or market.get("end_date_iso")
        if not end_str:
            continue
        try:
            end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue
        if not (now < end <= bonding_cutoff):
            continue

        condition_id = str(market.get("conditionId") or "").strip().lower()
        market_id = str(market.get("id") or market.get("conditionId") or "").lower()
        if not condition_id:
            continue
        if condition_id in excluded_ids or market_id in excluded_ids:
            continue
        aggregate = aggregates.get(condition_id)
        if not aggregate:
            continue

        signal = build_signal_from_aggregate(aggregate, len(traders))
        if not signal:
            continue
        if signal.get("traders_with_matching_positions", 0) < BONDING_MIN_MATCHING_TRADERS:
            continue

        odds_yes, odds_no = market_prices(market)
        side_price = odds_yes if signal["consensus_side"] == "YES" else odds_no
        if not (BONDING_MIN_PRICE <= side_price <= BONDING_MAX_PRICE):
            continue

        notional = signal["yes_weighted_notional"] + signal["no_weighted_notional"]
        hours_left = max((end - now).total_seconds() / 3600.0, 0.0)
        resolution_bonus = max(BONDING_MAX_HOURS_TO_RESOLUTION - hours_left, 0.0)
        score = (notional / 100.0) + (signal["confidence"] * 100.0) + (side_price * 100.0) + resolution_bonus
        if score > best_score:
            best_score = score
            best_market = market
            best_signal = dict(signal)
            best_signal["strategy"] = "bonding_copy"
            best_signal["consensus_side_price"] = round(side_price, 4)
            best_signal["hours_to_resolution"] = round(hours_left, 2)

    return best_market, best_signal


def resolve_workspace_root(argv):
    if len(argv) >= 2:
        return argv[1]
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    # stderr (not stdout) so callers parsing the decision JSON don't break.
    print(f"Logged trade: {question[:50]}... ({side} @ {odds})", file=sys.stderr)


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
        raise ValueError("no staged candidate for today")

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


def already_traded_today(workspace_root):
    trades_path = os.path.join(workspace_root, TRADES_FILE)
    if not os.path.exists(trades_path):
        return False
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(trades_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("date") == today:
                    return True
            except json.JSONDecodeError:
                continue
    return False


def already_decided_today(workspace_root):
    decisions_path = os.path.join(workspace_root, DECISIONS_FILE)
    if not os.path.exists(decisions_path):
        return False
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for entry in metrics.load_jsonl(decisions_path):
        if entry.get("date") == today:
            return True
    return False


def main():
    if len(sys.argv) <= 2:
        # Fetch and select (runs every 4h; geopolitical + crypto only; whale traders)
        workspace_root = resolve_workspace_root(sys.argv)
        excluded_ids = get_already_evaluated_ids(workspace_root, days=2)
        markets = fetch_markets()
        best, copy_signal = select_bonding_copy_candidate(markets, excluded_ids=excluded_ids)
        selection_source = "bonding_copy"
        if not best:
            best, copy_signal = select_copy_candidate(markets, excluded_ids=excluded_ids)
            selection_source = "whale_top_trader_copy"
        if not best:
            best = select_market(markets, excluded_ids=excluded_ids)
            selection_source = "volume_fallback"
        if not best:
            print(
                "No suitable geopolitical/crypto market found (whale positions, volume, closing within 7 days). "
                "Already evaluated in last 24h are excluded.",
                file=sys.stderr,
            )
            sys.exit(1)
        # outcomePrices: ["0.72","0.28"] for YES, NO (may be JSON string)
        odds_yes, odds_no = market_prices(best)
        out = {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "id": best.get("id") or best.get("conditionId"),
            "market_id": best.get("id") or best.get("conditionId"),
            "condition_id": best.get("conditionId"),
            "selection_source": selection_source,
            "question": best.get("question", ""),
            "odds_yes": odds_yes,
            "odds_no": odds_no,
            "volume": best.get("volume") or best.get("volumeNum"),
            "endDate": best.get("endDate") or best.get("end_date_iso"),
        }
        if copy_signal:
            out["copy_strategy"] = copy_signal
        else:
            out["copy_strategy"] = build_copy_signal(out.get("condition_id"), out["question"])
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

    if len(sys.argv) >= 7:
        # Log: workspace_root market_id side odds reasoning question
        workspace_root = sys.argv[1]
        market_id = sys.argv[2]
        side = sys.argv[3]
        odds = sys.argv[4]
        reasoning = sys.argv[5]
        question = " ".join(sys.argv[6:]) if len(sys.argv) > 6 else ""
        if side not in ("YES", "NO"):
            print("side must be YES or NO", file=sys.stderr)
            sys.exit(1)
        log_trade(workspace_root, market_id, question, side, odds, reasoning)
        return

    print(
        "usage: fetch mode: [workspace_root], staged log mode: workspace_root side reasoning, "
        "or full log mode: workspace_root market_id side odds reasoning question",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()

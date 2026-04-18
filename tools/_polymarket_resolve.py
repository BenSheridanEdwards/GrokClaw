#!/usr/bin/env python3
"""
Polymarket resolve: check unresolved trades against API, append results.
Stdlib only. Called from polymarket-resolve.sh.
"""
import json
import math
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from tools import _polymarket_metrics as metrics
from tools import _polymarket_ledger as ledger

API_BASE = "https://gamma-api.polymarket.com/markets"
TRADES_FILE = "data/polymarket-trades.json"
RESULTS_FILE = "data/polymarket-results.json"

# Grace-period resolution: Polymarket often leaves markets `closed: false` for days
# after the real-world outcome is known and prices have collapsed to a decisive
# extreme. Without a fallback, those trades sit in `open_exposure` forever and
# block new trades via the exposure cap.
RESOLVE_GRACE_HOURS = 6
RESOLVE_DECISIVE_THRESHOLD = 0.97


def fetch_market(market_id):
    url = f"{API_BASE}/{market_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "GrokClaw/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def parse_prices(raw_prices):
    prices = raw_prices or ["0.5", "0.5"]
    if isinstance(prices, str):
        prices = json.loads(prices) if prices.strip().startswith("[") else [prices, "0.5"]
    return [float(price) for price in prices]


def get_winning_index(market):
    prices = parse_prices(market.get("outcomePrices") or market.get("prices"))
    if len(prices) < 2:
        return None
    if prices[0] >= 0.999 and prices[1] <= 0.001:
        return 0
    if prices[1] >= 0.999 and prices[0] <= 0.001:
        return 1
    return None


def market_end_datetime(market):
    end_str = market.get("endDate") or market.get("end_date_iso")
    if not end_str:
        return None
    try:
        return datetime.fromisoformat(end_str.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def get_decisive_index(market, threshold=RESOLVE_DECISIVE_THRESHOLD):
    prices = parse_prices(market.get("outcomePrices") or market.get("prices"))
    if len(prices) < 2:
        return None
    if prices[0] >= threshold and prices[1] <= (1.0 - threshold):
        return 0
    if prices[1] >= threshold and prices[0] <= (1.0 - threshold):
        return 1
    return None


def market_past_end_with_decisive_price(market, now=None):
    end = market_end_datetime(market)
    if end is None:
        return False
    now = now or datetime.now(timezone.utc)
    if now < end + timedelta(hours=RESOLVE_GRACE_HOURS):
        return False
    return get_decisive_index(market) is not None


def market_is_resolved(market, now=None):
    if market.get("closed") is True and get_winning_index(market) is not None:
        return True
    return market_past_end_with_decisive_price(market, now=now)


def get_winning_side(market, now=None):
    winning_index = get_winning_index(market)
    if winning_index is None and market_past_end_with_decisive_price(market, now=now):
        winning_index = get_decisive_index(market)
    if winning_index == 0:
        return "YES"
    if winning_index == 1:
        return "NO"
    return None


def validate_odds(odds):
    value = float(odds)
    if not math.isfinite(value) or value <= 0 or value > 1:
        raise ValueError("odds must be a finite float in (0, 1]")
    return value


def pnl(odds, won):
    """WIN = (1/odds - 1) units; LOSS = -1 unit."""
    odds = validate_odds(odds)
    if won:
        return (1.0 / odds) - 1.0
    return -1.0


def _calibration_phrase(predicted_for_side, won):
    """Frame how miscalibrated the model was on this single trade.

    predicted_for_side is the model's probability of OUR side winning.
    """
    if predicted_for_side is None:
        return "no model probability recorded"
    actual = 1.0 if won else 0.0
    delta_pp = round((predicted_for_side - actual) * 100)
    if won and delta_pp <= 10:
        return f"model said {predicted_for_side*100:.0f}% — well-calibrated"
    if won and delta_pp <= 30:
        return f"model said {predicted_for_side*100:.0f}% — under-confident by {-delta_pp}pp"
    if won:
        return f"model said {predicted_for_side*100:.0f}% — under-confident by {-delta_pp}pp"
    if delta_pp >= 30:
        return f"model said {predicted_for_side*100:.0f}% — overconfident by {delta_pp}pp"
    if delta_pp >= 10:
        return f"model said {predicted_for_side*100:.0f}% — overconfident by {delta_pp}pp"
    return f"model said {predicted_for_side*100:.0f}% — close to coinflip"


def format_resolution_message(trade_record, result_record, workspace_root):
    """Build a Telegram one-block message with PnL, calibration, source/wallet stats."""
    question = (result_record.get("question") or "").strip() or "unknown market"
    short_q = question if len(question) <= 80 else question[:77] + "…"
    side = result_record.get("side") or trade_record.get("side") or "?"
    odds = result_record.get("odds") or trade_record.get("odds")
    odds_str = f"{float(odds)*100:.1f}¢" if odds else "?"
    winning_side = result_record.get("winning_side") or "?"
    won = bool(result_record.get("won"))
    stake = float(result_record.get("stake_amount") or 0.0)
    pnl_amount = float(result_record.get("pnl_amount") or 0.0)
    pnl_pct = (pnl_amount / stake * 100.0) if stake else 0.0
    outcome = "WIN" if won else "LOSS"

    prob_yes = result_record.get("probability_yes") or trade_record.get("probability_yes")
    if prob_yes is not None:
        try:
            predicted_for_side = float(prob_yes) if side == "YES" else 1.0 - float(prob_yes)
        except (TypeError, ValueError):
            predicted_for_side = None
    else:
        predicted_for_side = None
    calib = _calibration_phrase(predicted_for_side, won)

    source = result_record.get("selection_source") or trade_record.get("selection_source") or "unknown"
    src_stats = ledger.source_stats(source, workspace_root=workspace_root)
    src_mul = ledger.source_stake_multiplier(source, workspace_root=workspace_root)
    if src_stats["samples"] == 0:
        src_line = f"Source {source}: first resolved trade"
    else:
        wr_str = f"{(src_stats['win_rate'] or 0)*100:.0f}%" if src_stats["win_rate"] is not None else "n/a"
        kill_tag = " · 0.5× stake ACTIVE" if src_mul < 1.0 else ""
        src_line = (
            f"Source {source}: {src_stats['wins']}W-{src_stats['losses']}L last "
            f"{src_stats['samples']} ({wr_str}) · PnL ${src_stats['pnl']:+.2f}{kill_tag}"
        )

    wallets = result_record.get("wallets") or trade_record.get("wallets") or []
    wallet_lines = []
    for w in wallets[:3]:
        ws = ledger.wallet_stats(w, workspace_root=workspace_root)
        weight = ledger.wallet_blend_weight(w, workspace_root=workspace_root)
        wallet_lines.append(
            f"Wallet {ledger.short_wallet(w)}: {ws['wins']}W-{ws['losses']}L · weight {weight:.2f}"
        )

    similar = ledger.similar_recent_losses(question, source, workspace_root=workspace_root)
    similarity_line = ""
    if not won and similar:
        similarity_line = f"Loss similarity: {len(similar)} prior losses on {source} with overlapping topic"

    lines = [
        f"Resolved · {outcome} ${pnl_amount:+.2f} ({pnl_pct:+.0f}%)",
        short_q,
        f"{side} @ {odds_str} → settled {winning_side} · {calib}",
        src_line,
    ]
    lines.extend(wallet_lines)
    if similarity_line:
        lines.append(similarity_line)
    return "\n".join(lines)


def post_resolution_to_telegram(workspace_root, message):
    script = os.path.join(workspace_root, "tools", "telegram-post.sh")
    if not os.path.exists(script):
        return
    try:
        subprocess.run(
            [script, "polymarket", message],
            cwd=workspace_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:
        print(f"telegram-post failed: {exc}", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print("usage: _polymarket_resolve.py <workspace_root>", file=sys.stderr)
        sys.exit(1)
    workspace_root = sys.argv[1]
    trades_path = os.path.join(workspace_root, TRADES_FILE)
    results_path = os.path.join(workspace_root, RESULTS_FILE)
    os.makedirs(os.path.dirname(results_path), exist_ok=True)

    if not os.path.exists(trades_path):
        sys.exit(0)

    # Read trades, find unresolved
    trades = []
    with open(trades_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                trades.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    updated_trades = []
    resolved_count = 0
    for t in trades:
        if t.get("resolved"):
            updated_trades.append(t)
            continue
        market_id = t.get("market_id")
        market = fetch_market(market_id)
        if not market or not market_is_resolved(market):
            updated_trades.append(t)
            continue
        winning = get_winning_side(market)
        if winning is None:
            updated_trades.append(t)
            continue
        side = t.get("side", "YES")
        try:
            odds = validate_odds(t.get("odds", 0.5))
        except (TypeError, ValueError) as exc:
            print(f"Skipping trade with invalid odds for market {market_id}: {exc}", file=sys.stderr)
            updated_trades.append(t)
            continue
        won = side == winning
        pnl_val = pnl(odds, won)
        t["resolved"] = True
        t["resolved_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stake_amount = round(float(t.get("stake_amount", 1.0)), 2)
        pnl_amount = round(stake_amount * pnl_val, 2)
        bankroll_entry = metrics.record_bankroll_event(
            workspace_root,
            {
                "date": t["resolved_at"],
                "kind": "resolved_trade",
                "market_id": market_id,
                "question": t.get("question", ""),
                "delta": pnl_amount,
            },
        )
        updated_trades.append(t)
        result = {
            "date": t.get("date"),
            "resolved_at": t["resolved_at"],
            "market_id": market_id,
            "question": t.get("question"),
            "side": side,
            "odds": odds,
            "won": won,
            "winning_side": winning,
            "pnl": round(pnl_val, 4),
            "stake_amount": stake_amount,
            "pnl_amount": pnl_amount,
            "probability_yes": t.get("probability_yes"),
            "model_probability": t.get("model_probability"),
            "market_probability": t.get("market_probability"),
            "edge": t.get("edge"),
            "selection_source": t.get("selection_source"),
            "wallets": t.get("wallets") or [],
            "confidence": t.get("confidence"),
            "bankroll_before": bankroll_entry["bankroll_before"],
            "bankroll_after": bankroll_entry["bankroll_after"],
        }
        with open(results_path, "a") as f:
            f.write(json.dumps(result) + "\n")
        resolved_count += 1
        print(
            f"Resolved: {t.get('question', '')[:50]}... "
            f"{'WIN' if won else 'LOSS'} (P&L: {pnl_amount:+.2f}, bankroll: {bankroll_entry['bankroll_after']:+.2f})",
            file=sys.stderr,
        )
        try:
            telegram_message = format_resolution_message(t, result, workspace_root)
            post_resolution_to_telegram(workspace_root, telegram_message)
        except Exception as exc:
            print(f"resolution telegram skipped: {exc}", file=sys.stderr)

    # Write back updated trades (with resolved=True)
    with open(trades_path, "w") as f:
        for t in updated_trades:
            f.write(json.dumps(t) + "\n")

    if resolved_count > 0:
        print(f"Resolved {resolved_count} trade(s), appended to {RESULTS_FILE}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Polymarket digest: aggregate past 7 days, format Slack message, suggest improvement.
Stdlib only. Called from polymarket-digest.sh.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from tools import _polymarket_metrics as metrics

RESULTS_FILE = "data/polymarket-results.json"
DIGEST_STATE_FILE = "data/polymarket-digest-state.json"


def parse_result_date(result):
    date_str = result.get("resolved_at") or result.get("date", "")
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def load_recent_results(results_path, now):
    cutoff = now - timedelta(days=7)
    results = []
    if not os.path.exists(results_path):
        return results

    with open(results_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                result = json.loads(line)
                if parse_result_date(result) >= cutoff:
                    results.append(result)
            except (json.JSONDecodeError, ValueError):
                continue
    return results


def build_payload(slack_msg, improvement):
    return "DIGEST_JSON:" + json.dumps(
        {"slack_msg": slack_msg, "improvement": improvement},
        separators=(",", ":"),
    )


def digest_week_key(now):
    return now.strftime("%G-W%V")


def digest_already_recorded(workspace_root, now):
    state_path = os.path.join(workspace_root, DIGEST_STATE_FILE)
    if not os.path.exists(state_path):
        return False
    try:
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return False
    return state.get("week_key") == digest_week_key(now)


def mark_digest_recorded(workspace_root, now):
    state_path = os.path.join(workspace_root, DIGEST_STATE_FILE)
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as handle:
        json.dump({"week_key": digest_week_key(now), "recorded_at": now.strftime("%Y-%m-%d")}, handle)


def main():
    if len(sys.argv) < 2:
        print("usage: _polymarket_digest.py <workspace_root>", file=sys.stderr)
        sys.exit(1)
    workspace_root = sys.argv[1]
    results_path = os.path.join(workspace_root, RESULTS_FILE)

    now = datetime.now(timezone.utc)
    results = load_recent_results(results_path, now)
    summary = metrics.summarize(workspace_root, days=7)
    promotion = metrics.check_promotion_gate(metrics.summarize(workspace_root))

    if not results:
        msg = (
            "📊 *Polymarket Weekly Digest* (past 7 days)\n"
            f"• Bankroll: ${summary['current_bankroll']:.2f}\n"
            "• No resolved trades in this period."
        )
        print(build_payload(msg, "No trades to analyze this week."))
        return

    wins = summary["wins"]
    total = summary["resolved_count"]
    accuracy = 100.0 * summary["accuracy"]
    total_pnl = summary["total_pnl"]
    best = max(results, key=lambda r: r.get("pnl", -999))
    worst = min(results, key=lambda r: r.get("pnl", 999))
    brier = summary["brier_score"]
    drawdown = summary["max_drawdown"] * 100.0

    msg = (
        f"📊 *Polymarket Weekly Digest* (past 7 days)\n"
        f"• Bankroll: ${summary['current_bankroll']:.2f}\n"
        f"• Accuracy: {wins}/{total} ({accuracy:.0f}%)\n"
        f"• Total paper P&L: ${total_pnl:+.2f}\n"
        f"• Skip count: {summary['skip_count']}\n"
        f"• Max drawdown: {drawdown:.1f}%\n"
        f"• Brier score: {'n/a' if brier is None else f'{brier:.3f}'}\n"
        f"• Best call: {best.get('question', '')[:60]}... ({'WIN' if best.get('won') else 'LOSS'}, ${best.get('pnl_amount', 0):+.2f})\n"
        f"• Worst call: {worst.get('question', '')[:60]}... ({'WIN' if worst.get('won') else 'LOSS'}, ${worst.get('pnl_amount', 0):+.2f})\n"
        f"• Promotion gate: {'PASS' if promotion['eligible'] else 'BLOCKED'}"
    )

    # Self-improvement note
    if brier is not None and brier <= 0.10 and total_pnl > 0:
        improvement = "Polymarket: Calibrated and profitable week. Keep the same gates and sizing."
    elif accuracy >= 70:
        improvement = f"Polymarket: Strong week ({accuracy:.0f}% accuracy). Continue current approach."
    elif accuracy >= 50 or total_pnl >= 0:
        improvement = (
            f"Polymarket: Mixed week ({accuracy:.0f}% accuracy, ${total_pnl:+.2f}). "
            "Review the worst call and skipped edges for calibration."
        )
    else:
        improvement = (
            f"Polymarket: Tough week ({accuracy:.0f}% accuracy, ${total_pnl:+.2f}). "
            "Tighten confidence thresholds and reduce aggressive estimates."
        )
    print(build_payload(msg, improvement))


if __name__ == "__main__":
    main()

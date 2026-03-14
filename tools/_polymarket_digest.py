#!/usr/bin/env python3
"""
Polymarket digest: aggregate past 7 days, format Slack message, suggest improvement.
Stdlib only. Called from polymarket-digest.sh.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

RESULTS_FILE = "data/polymarket-results.json"


def main():
    if len(sys.argv) < 2:
        print("usage: _polymarket_digest.py <workspace_root>", file=sys.stderr)
        sys.exit(1)
    workspace_root = sys.argv[1]
    results_path = os.path.join(workspace_root, RESULTS_FILE)
    memory_path = os.path.join(workspace_root, "memory", "MEMORY.md")

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)
    results = []
    if os.path.exists(results_path):
        with open(results_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    date_str = r.get("date", "")
                    try:
                        r_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        if r_date >= cutoff:
                            results.append(r)
                    except ValueError:
                        results.append(r)
                except json.JSONDecodeError:
                    continue

    if not results:
        msg = (
            "📊 *Polymarket Weekly Digest* (past 7 days)\n"
            "No resolved trades in this period."
        )
        print("SLACK_MSG:" + msg)
        print("IMPROVEMENT:No trades to analyze this week.")
        return

    wins = sum(1 for r in results if r.get("won"))
    total = len(results)
    accuracy = (100.0 * wins / total) if total else 0
    total_pnl = sum(r.get("pnl", 0) for r in results)
    best = max(results, key=lambda r: r.get("pnl", -999))
    worst = min(results, key=lambda r: r.get("pnl", 999))

    msg = (
        f"📊 *Polymarket Weekly Digest* (past 7 days)\n"
        f"• Accuracy: {wins}/{total} ({accuracy:.0f}%)\n"
        f"• Total paper P&L: {total_pnl:+.2f} units\n"
        f"• Best call: {best.get('question', '')[:60]}... ({'WIN' if best.get('won') else 'LOSS'}, {best.get('pnl', 0):+.2f})\n"
        f"• Worst call: {worst.get('question', '')[:60]}... ({'WIN' if worst.get('won') else 'LOSS'}, {worst.get('pnl', 0):+.2f})"
    )
    print("SLACK_MSG:" + msg)

    # Self-improvement note
    if accuracy >= 70:
        improvement = f"Polymarket: Strong week ({accuracy:.0f}% accuracy). Continue current approach."
    elif accuracy >= 50:
        improvement = f"Polymarket: Moderate week ({accuracy:.0f}% accuracy). Review worst call for calibration."
    else:
        improvement = f"Polymarket: Tough week ({accuracy:.0f}% accuracy). Revisit reasoning on high-conviction bets."
    print("IMPROVEMENT:" + improvement)
    print("MEMORY_PATH:" + memory_path)


if __name__ == "__main__":
    main()

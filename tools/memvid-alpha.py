#!/usr/bin/env python3
"""
Memvid alpha-polymarket memory: ingest decisions/results or query the capsule.
Stdlib only (no external deps beyond memvid-sdk).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPSULE_PATH = os.path.join(
    WORKSPACE_ROOT, "data", "alpha", "memory", "alpha-polymarket.mv2"
)

try:
    from memvid_sdk import create, use
except ImportError:
    print("memvid-sdk not installed: pip install memvid-sdk", file=sys.stderr)
    sys.exit(1)


def open_capsule():
    if not os.path.exists(CAPSULE_PATH):
        mem = create(CAPSULE_PATH, "basic")
    else:
        mem = use("basic", CAPSULE_PATH)
    return mem


def ingest_decision(mem, decision: dict) -> str:
    d = decision
    outcome_won = None
    if d.get("resolved"):
        outcome_won = d.get("won")

    text_parts = [
        f"Date: {d.get('date')}",
        f"Market: {d.get('question')}",
        f"Market ID: {d.get('market_id')}",
        f"Side: {d.get('side')}",
        f"Action: {d.get('action')}",
        f"Market probability: {d.get('market_probability')}",
        f"Model probability: {d.get('model_probability')}",
        f"Whale consensus probability: {d.get('whale_consensus_probability')}",
        f"Whale confidence: {d.get('whale_confidence')}",
        f"Whale traders: {d.get('whale_traders')}",
        f"Selection source: {d.get('selection_source')}",
        f"Edge: {d.get('edge')}",
        f"Confidence: {d.get('confidence')}",
        f"Volume: {d.get('volume')}",
        f"Stake amount: {d.get('stake_amount')}",
        f"Bankroll before: {d.get('bankroll_before')}",
        f"Gate failures: {', '.join(d.get('gate_failures') or [])}",
        f"Reasoning: {d.get('reasoning', '').strip()}",
    ]
    text = "\n".join(text_parts)

    label = "decision"
    title = (
        f"{d.get('date')} {d.get('action').upper()} {str(d.get('question', ''))[:60]}"
    )

    mem.put(
        title=title,
        label=label,
        metadata={
            "date": d.get("date"),
            "market_id": str(d.get("market_id", "")),
            "action": d.get("action"),
            "side": d.get("side"),
            "won": outcome_won,
            "edge": d.get("edge"),
            "volume": d.get("volume"),
            "whale_traders": d.get("whale_traders"),
            "selection_source": d.get("selection_source"),
        },
        text=text,
    )
    return title


def ingest_result(mem, result: dict) -> str:
    r = result
    text_parts = [
        f"Resolution Date: {r.get('resolved_at') or r.get('date')}",
        f"Market: {r.get('question')}",
        f"Market ID: {r.get('market_id')}",
        f"Traded side: {r.get('side')}",
        f"Odds: {r.get('odds')}",
        f"Won: {r.get('won')}",
        f"Winning side: {r.get('winning_side')}",
        f"PnL: {r.get('pnl_amount')}",
        f"Stake: {r.get('stake_amount')}",
        f"Probability YES (model): {r.get('probability_yes')}",
        f"Probability YES (market): {r.get('market_probability')}",
        f"Edge: {r.get('edge')}",
        f"Bankroll before: {r.get('bankroll_before')}",
        f"Bankroll after: {r.get('bankroll_after')}",
    ]
    text = "\n".join(text_parts)

    label = "result"
    title = f"{r.get('resolved_at', 'unknown')} {'WIN' if r.get('won') else 'LOSS'} {str(r.get('question', ''))[:60]}"

    mem.put(
        title=title,
        label=label,
        metadata={
            "date": r.get("date"),
            "resolved_at": r.get("resolved_at"),
            "market_id": str(r.get("market_id", "")),
            "won": r.get("won"),
            "pnl_amount": r.get("pnl_amount"),
            "edge": r.get("edge"),
            "volume": r.get("volume"),
        },
        text=text,
    )
    return title


def query_memvid(mem, query: str, k: int = 5) -> str:
    results = mem.find(query, k=k, mode="lex", snippet_chars=600)
    if not results.get("hits"):
        return "No relevant memory found."

    lines = ["## Memvid Memory Search Results\n"]
    for i, hit in enumerate(results["hits"], 1):
        meta = hit.get("metadata", {})
        title = hit.get("title", "Untitled")
        won = meta.get("won")
        lines.append(f"### [{i}] {title}")
        if won is not None:
            lines.append(f"Outcome: {'WIN' if won else 'LOSS'}")
        if meta.get("edge") is not None:
            lines.append(f"Edge: {meta['edge']}")
        if meta.get("whale_traders") is not None:
            lines.append(f"Whale traders: {meta['whale_traders']}")
        if meta.get("selection_source"):
            lines.append(f"Selection source: {meta['selection_source']}")
        snippet = hit.get("text", "")[:500]
        lines.append(f"Snippet: {snippet}")
        lines.append("")
    return "\n".join(lines)


def query_recent_trades(mem, k: int = 5) -> str:
    results = mem.find("trade action", k=k, mode="lex")
    if not results.get("hits"):
        return "No past trades found."
    lines = ["## Recent Trades from Memory\n"]
    for i, hit in enumerate(results["hits"], 1):
        meta = hit.get("metadata", {})
        title = hit.get("title", "Untitled")
        outcome = (
            "WIN"
            if meta.get("won")
            else ("LOSS" if meta.get("won") is False else "pending")
        )
        edge = meta.get("edge")
        edge_str = f"edge={edge}" if edge is not None else ""
        lines.append(f"[{i}] {title} — {outcome} {edge_str}")
    return "\n".join(lines)


def query_whale_accuracy(mem, k: int = 5) -> str:
    results = mem.find("whale traders", k=k, mode="lex")
    if not results.get("hits"):
        return "No whale-backed decisions found."
    lines = ["## Past Whale-Backed Decisions\n"]
    for i, hit in enumerate(results["hits"], 1):
        meta = hit.get("metadata", {})
        title = hit.get("title", "Untitled")
        traders = meta.get("whale_traders")
        won = meta.get("won")
        edge = meta.get("edge")
        traders_str = f"whales={traders}" if traders else "whales unknown"
        won_str = "WIN" if won else ("LOSS" if won is False else "pending")
        edge_str = f"edge={edge}" if edge is not None else ""
        lines.append(f"[{i}] {title} — {won_str}, {traders_str}, {edge_str}")
    return "\n".join(lines)


def query_whale_accuracy(mem, k: int = 5) -> str:
    results = mem.find("whale consensus prediction", k=k, mode="hybrid")
    if not results.get("hits"):
        return "No whale-backed decisions found."
    lines = ["## Past Whale-Backed Decisions\n"]
    for i, hit in enumerate(results["hits"], 1):
        meta = hit.get("metadata", {})
        lines.append(f"[{i}] {hit.get('title', '')}")
        if meta.get("whale_traders"):
            lines.append(
                f"  Whales: {meta['whale_traders']}, edge: {meta.get('edge')}, won: {meta.get('won')}"
            )
    return "\n".join(lines)


def bulk_ingest_decisions(mem, decisions_path: str) -> int:
    count = 0
    rows = []
    with open(decisions_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    for d in rows:
        if d.get("action") == "trade":
            ingest_decision(mem, d)
            count += 1
    return count


def bulk_ingest_results(mem, results_path: str) -> int:
    count = 0
    rows = []
    with open(results_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    for r in rows:
        if r.get("won") is not None:
            ingest_result(mem, r)
            count += 1
    return count


USAGE = """
Usage:
  memvid-alpha.py ingest-decision <decision.json>
  memvid-alpha.py ingest-decision --latest   # ingest last decision from data/polymarket-decisions.json
  memvid-alpha.py ingest-result <result.json>
  memvid-alpha.py ingest-result --latest     # ingest last resolved result from data/polymarket-results.json
  memvid-alpha.py ingest-history
  memvid-alpha.py query <question>
  memvid-alpha.py recent-trades
  memvid-alpha.py whale-accuracy
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    mem = open_capsule()

    if cmd == "ingest-decision":
        if len(sys.argv) < 3:
            print("usage: ingest-decision <decision.json>", file=sys.stderr)
            sys.exit(1)
        arg = sys.argv[2]
        if arg == "--latest":
            decisions_path = os.path.join(
                WORKSPACE_ROOT, "data", "polymarket-decisions.json"
            )
            with open(decisions_path, encoding="utf-8") as f:
                rows = [json.loads(l) for l in f if l.strip()]
            if not rows:
                print("No decisions to ingest", file=sys.stderr)
                sys.exit(1)
            decision = rows[-1]
        else:
            with open(arg, encoding="utf-8") as f:
                decision = json.load(f)
        title = ingest_decision(mem, decision)
        print(f"Ingested decision: {title}")

    elif cmd == "ingest-result":
        if len(sys.argv) < 3:
            print("usage: ingest-result <result.json>", file=sys.stderr)
            sys.exit(1)
        arg = sys.argv[2]
        if arg == "--latest":
            results_path = os.path.join(
                WORKSPACE_ROOT, "data", "polymarket-results.json"
            )
            with open(results_path, encoding="utf-8") as f:
                rows = [
                    json.loads(l)
                    for l in f
                    if l.strip() and json.loads(l).get("won") is not None
                ]
            if not rows:
                print("No resolved results to ingest", file=sys.stderr)
                sys.exit(1)
            result = rows[-1]
        else:
            with open(arg, encoding="utf-8") as f:
                result = json.load(f)
        title = ingest_result(mem, result)
        print(f"Ingested result: {title}")

    elif cmd == "ingest-history":
        ws = WORKSPACE_ROOT
        decisions_path = os.path.join(ws, "data", "polymarket-decisions.json")
        results_path = os.path.join(ws, "data", "polymarket-results.json")
        dc = (
            bulk_ingest_decisions(mem, decisions_path)
            if os.path.exists(decisions_path)
            else 0
        )
        rs = (
            bulk_ingest_results(mem, results_path)
            if os.path.exists(results_path)
            else 0
        )
        print(f"History ingested: {dc} decisions, {rs} results")

    elif cmd == "query":
        if len(sys.argv) < 3:
            print("usage: query <question>", file=sys.stderr)
            sys.exit(1)
        print(query_memvid(mem, sys.argv[2]))

    elif cmd == "recent-trades":
        print(query_recent_trades(mem))

    elif cmd == "whale-accuracy":
        print(query_whale_accuracy(mem))

    else:
        print(f"Unknown command: {cmd}{USAGE}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
MemPalace alpha-polymarket memory backend.
Stdlib only, JSONL-backed, deterministic/deduplicated summaries.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[1]))
MEMORY_FILE = WORKSPACE_ROOT / "data" / "alpha" / "memory" / "mempalace-alpha.jsonl"
DECISIONS_FILE = WORKSPACE_ROOT / "data" / "polymarket-decisions.json"
RESULTS_FILE = WORKSPACE_ROOT / "data" / "polymarket-results.json"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def record_key(record: dict[str, Any]) -> str:
    return "|".join(
        [
            str(record.get("kind", "")),
            str(record.get("date", "")),
            str(record.get("market_id", "")),
            str(record.get("action", record.get("side", ""))),
        ]
    )


def dedup_append(path: Path, payload: dict[str, Any]) -> None:
    existing = load_jsonl(path)
    key = record_key(payload)
    keys = {record_key(item) for item in existing}
    if key in keys:
        return
    append_jsonl(path, payload)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ingest_decision(decision: dict[str, Any]) -> str:
    payload = {
        "kind": "decision",
        "ingested_at": now_iso(),
        "date": decision.get("date"),
        "market_id": decision.get("market_id"),
        "question": decision.get("question"),
        "side": decision.get("side"),
        "action": decision.get("action"),
        "market_probability": decision.get("market_probability"),
        "model_probability": decision.get("model_probability"),
        "probability_yes": decision.get("probability_yes"),
        "edge": decision.get("edge"),
        "confidence": decision.get("confidence"),
        "volume": decision.get("volume"),
        "stake_amount": decision.get("stake_amount"),
        "whale_traders": decision.get("whale_traders"),
        "selection_source": decision.get("selection_source"),
        "reasoning": decision.get("reasoning"),
    }
    dedup_append(MEMORY_FILE, payload)
    title = f"{payload.get('date')} {str(payload.get('action', '')).upper()} {str(payload.get('question', ''))[:60]}"
    return title


def ingest_result(result: dict[str, Any]) -> str:
    payload = {
        "kind": "result",
        "ingested_at": now_iso(),
        "date": result.get("date"),
        "resolved_at": result.get("resolved_at"),
        "market_id": result.get("market_id"),
        "question": result.get("question"),
        "side": result.get("side"),
        "winning_side": result.get("winning_side"),
        "won": result.get("won"),
        "pnl_amount": result.get("pnl_amount"),
        "stake_amount": result.get("stake_amount"),
        "probability_yes": result.get("probability_yes"),
        "market_probability": result.get("market_probability"),
        "edge": result.get("edge"),
    }
    dedup_append(MEMORY_FILE, payload)
    status = "WIN" if payload.get("won") else "LOSS"
    title = f"{payload.get('resolved_at', 'unknown')} {status} {str(payload.get('question', ''))[:60]}"
    return title


def latest_from_file(path: Path) -> dict[str, Any] | None:
    rows = load_jsonl(path)
    if not rows:
        return None
    return rows[-1]


def latest_resolved_result(path: Path) -> dict[str, Any] | None:
    rows = [row for row in load_jsonl(path) if row.get("won") is not None]
    if not rows:
        return None
    return rows[-1]


def token_set(text: str) -> set[str]:
    return {tok for tok in "".join(c.lower() if c.isalnum() else " " for c in text).split() if tok}


def query_records(query: str, k: int = 5) -> list[dict[str, Any]]:
    records = load_jsonl(MEMORY_FILE)
    if not records:
        return []
    q = token_set(query)
    scored: list[tuple[float, dict[str, Any]]] = []
    for rec in records:
        text = " ".join(
            [
                str(rec.get("question", "")),
                str(rec.get("reasoning", "")),
                str(rec.get("selection_source", "")),
                str(rec.get("side", "")),
                str(rec.get("action", "")),
            ]
        )
        r = token_set(text)
        overlap = len(q & r)
        if overlap <= 0:
            continue
        scored.append((float(overlap), rec))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [rec for _, rec in scored[:k]]


def format_recent_trades(k: int = 5) -> str:
    records = [r for r in load_jsonl(MEMORY_FILE) if r.get("kind") == "decision" and r.get("action") == "trade"]
    if not records:
        return "No past trades found."
    results_by_market: dict[str, dict[str, Any]] = {}
    for r in load_jsonl(MEMORY_FILE):
        if r.get("kind") == "result":
            results_by_market[str(r.get("market_id"))] = r
    lines = ["## Recent Trades from Memory", ""]
    for idx, rec in enumerate(records[-k:][::-1], start=1):
        market_id = str(rec.get("market_id"))
        result = results_by_market.get(market_id)
        if result is None:
            outcome = "pending"
        else:
            outcome = "WIN" if result.get("won") else "LOSS"
        edge = rec.get("edge")
        edge_str = f"edge={edge}" if edge is not None else ""
        lines.append(f"[{idx}] {rec.get('date')} TRADE {str(rec.get('question', ''))[:60]} — {outcome} {edge_str}")
    return "\n".join(lines)


def format_whale_accuracy(k: int = 5) -> str:
    records = [
        r
        for r in load_jsonl(MEMORY_FILE)
        if r.get("kind") == "decision"
        and (
            (r.get("whale_traders") or 0) > 0
            or str(r.get("selection_source", "")).startswith("bonding")
            or "whale" in str(r.get("selection_source", ""))
        )
    ]
    if not records:
        return "No whale-backed decisions found."
    results_by_market: dict[str, dict[str, Any]] = {}
    for r in load_jsonl(MEMORY_FILE):
        if r.get("kind") == "result":
            results_by_market[str(r.get("market_id"))] = r
    lines = ["## Past Whale-Backed Decisions", ""]
    for idx, rec in enumerate(records[-k:][::-1], start=1):
        market_id = str(rec.get("market_id"))
        result = results_by_market.get(market_id)
        if result is None:
            outcome = "pending"
        else:
            outcome = "WIN" if result.get("won") else "LOSS"
        lines.append(
            f"[{idx}] {rec.get('date')} {str(rec.get('action', '')).upper()} {str(rec.get('question', ''))[:60]} "
            f"— {outcome}, whales={rec.get('whale_traders')}, edge={rec.get('edge')}"
        )
    return "\n".join(lines)


USAGE = """
Usage:
  mempalace-alpha.py ingest-decision <decision.json>
  mempalace-alpha.py ingest-decision --latest
  mempalace-alpha.py ingest-result <result.json>
  mempalace-alpha.py ingest-result --latest
  mempalace-alpha.py ingest-history
  mempalace-alpha.py query <question>
  mempalace-alpha.py recent-trades
  mempalace-alpha.py whale-accuracy
"""


def main() -> int:
    if len(sys.argv) < 2:
        print(USAGE, file=sys.stderr)
        return 1

    cmd = sys.argv[1]
    if cmd == "ingest-decision":
        if len(sys.argv) < 3:
            print("usage: ingest-decision <decision.json>|--latest", file=sys.stderr)
            return 1
        arg = sys.argv[2]
        if arg == "--latest":
            decision = latest_from_file(DECISIONS_FILE)
            if decision is None:
                print("No decisions to ingest", file=sys.stderr)
                return 1
        else:
            decision = json.loads(Path(arg).read_text(encoding="utf-8"))
        print(f"Ingested decision: {ingest_decision(decision)}")
        return 0

    if cmd == "ingest-result":
        if len(sys.argv) < 3:
            print("usage: ingest-result <result.json>|--latest", file=sys.stderr)
            return 1
        arg = sys.argv[2]
        if arg == "--latest":
            result = latest_resolved_result(RESULTS_FILE)
            if result is None:
                print("No resolved results to ingest", file=sys.stderr)
                return 1
        else:
            result = json.loads(Path(arg).read_text(encoding="utf-8"))
        print(f"Ingested result: {ingest_result(result)}")
        return 0

    if cmd == "ingest-history":
        dc = 0
        rc = 0
        for d in load_jsonl(DECISIONS_FILE):
            ingest_decision(d)
            dc += 1
        for r in load_jsonl(RESULTS_FILE):
            if r.get("won") is not None:
                ingest_result(r)
                rc += 1
        print(f"History ingested: {dc} decisions, {rc} results")
        return 0

    if cmd == "query":
        if len(sys.argv) < 3:
            print("usage: query <question>", file=sys.stderr)
            return 1
        hits = query_records(sys.argv[2])
        if not hits:
            print("No relevant memory found.")
            return 0
        lines = ["## MemPalace Memory Search Results", ""]
        for idx, rec in enumerate(hits, start=1):
            lines.append(
                f"[{idx}] {rec.get('date')} {str(rec.get('action', rec.get('kind', ''))).upper()} "
                f"{str(rec.get('question', ''))[:80]} | edge={rec.get('edge')} | src={rec.get('selection_source')}"
            )
        print("\n".join(lines))
        return 0

    if cmd == "recent-trades":
        print(format_recent_trades())
        return 0

    if cmd == "whale-accuracy":
        print(format_whale_accuracy())
        return 0

    print(f"Unknown command: {cmd}\n{USAGE}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

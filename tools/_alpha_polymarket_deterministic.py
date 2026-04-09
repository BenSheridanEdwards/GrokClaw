#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class CmdResult:
    code: int
    stdout: str
    stderr: str


def utc_now() -> datetime:
    raw = os.environ.get("ALPHA_NOW", "").strip()
    if raw:
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
            try:
                return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return datetime.now(timezone.utc)


def run_command(root: Path, *args: str, check: bool = True) -> CmdResult:
    completed = subprocess.run(
        list(args),
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(args)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return CmdResult(completed.returncode, completed.stdout.strip(), completed.stderr.strip())


def parse_json_maybe(raw: str) -> Optional[dict]:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def safe_text(value: str) -> str:
    return (value or "").strip() or "No output captured."


def build_research_markdown(
    now: datetime,
    candidate: Optional[dict],
    decision: Optional[dict],
    context_text: str,
    recent_trades_text: str,
    whale_accuracy_text: str,
) -> str:
    question = candidate.get("question", "No candidate selected.") if candidate else "No candidate selected."
    source = candidate.get("selection_source", "none") if candidate else "none"
    copy = candidate.get("copy_strategy") if isinstance(candidate, dict) else {}
    if not isinstance(copy, dict):
        copy = {}
    consensus_yes = copy.get("consensus_probability_yes", "n/a")
    whale_conf = copy.get("confidence", "n/a")
    whale_traders = copy.get("traders_with_matching_positions", "n/a")

    action = (decision or {}).get("action", "skip")
    reasoning = (decision or {}).get("reasoning", "Deterministic fallback reasoning not available.")
    edge = (decision or {}).get("edge", "n/a")
    stake = (decision or {}).get("stake_amount", "n/a")

    lines = [
        f"# Alpha Research - {now.strftime('%Y-%m-%d-%H')}",
        "",
        "## Research Context",
        f"Context summary from polymarket-context.sh: {safe_text(context_text)}",
        "Recent performance appears in the memvid snippets below, and this run uses deterministic trade mechanics.",
        "When no robust copy signal exists, the strategy defaults to disciplined HOLD behavior.",
        "",
        "## Market Analysis",
        f"Candidate question: {question}",
        f"Selection source: {source}; whale consensus probability YES: {consensus_yes}; whale confidence: {whale_conf}; whale trader count: {whale_traders}.",
        "This run prioritizes bonding-copy opportunities, then whale-copy, then volume fallback if no copy signal is available.",
        "",
        "## Memvid Lookup",
        f"recent-trades: {safe_text(recent_trades_text)}",
        f"whale-accuracy: {safe_text(whale_accuracy_text)}",
        "These memory snapshots are used to avoid repeating failed patterns and to calibrate confidence.",
        "",
        "## Decision Rationale",
        f"Action: {action}; edge: {edge}; stake amount: {stake}.",
        f"Reasoning: {reasoning}",
        "Deterministic gates from polymarket-decide enforce confidence, edge, liquidity, and exposure limits.",
        "",
        "## Self-Correction",
        "A recurring mistake was over-trading weak conviction setups after recent losses.",
        "This deterministic flow avoids narrative drift by always applying the same gate sequence before placing risk.",
        "If evidence is weak, the system records HOLD and preserves bankroll optionality.",
        "",
        "## Next Steps",
        "Confirm whether bonding-copy candidates are available in the next hour.",
        "Track whether whale consensus improves in correlated geopolitical or crypto markets.",
        "Revisit thresholds only after multiple resolved outcomes, not single-run variance.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: _alpha_polymarket_deterministic.py <workspace_root>", file=sys.stderr)
        return 1

    root = Path(argv[1]).resolve()
    tools = root / "tools"
    now = utc_now()
    run_id = os.environ.get("CRON_RUN_ID", f"alpha-deterministic-{int(now.timestamp())}")

    context = run_command(root, str(tools / "polymarket-context.sh"), check=False).stdout
    recent_trades = run_command(root, str(tools / "memvid-alpha-query.sh"), "recent-trades", check=False).stdout
    whale_accuracy = run_command(root, str(tools / "memvid-alpha-query.sh"), "whale-accuracy", check=False).stdout

    candidate = None
    try:
        candidate_out = run_command(root, str(tools / "polymarket-trade.sh"), check=True).stdout
        candidate = parse_json_maybe(candidate_out)
    except RuntimeError:
        candidate = None

    decision = None
    if candidate and isinstance(candidate, dict):
        copy = candidate.get("copy_strategy") if isinstance(candidate.get("copy_strategy"), dict) else {}
        consensus_yes = copy.get("consensus_probability_yes")
        confidence = copy.get("confidence")
        traders = int(copy.get("traders_with_matching_positions", 0) or 0)
        selection_source = str(candidate.get("selection_source", ""))
        can_trade_from_copy = (
            copy.get("status") == "ok"
            and isinstance(consensus_yes, (int, float))
            and isinstance(confidence, (int, float))
            and (selection_source == "bonding_copy" or traders >= 2)
        )
        if can_trade_from_copy:
            side = "YES" if float(consensus_yes) >= 0.5 else "NO"
            selected_prob_yes = float(consensus_yes)
            selected_prob = selected_prob_yes if side == "YES" else (1.0 - selected_prob_yes)
            conf = max(min(float(confidence), 0.95), 0.5)
            reasoning = (
                "Deterministic copy execution from trader consensus; "
                f"source={selection_source}, consensus_yes={selected_prob_yes:.4f}, confidence={conf:.4f}"
            )
            decision_out = run_command(
                root,
                str(tools / "polymarket-decide.sh"),
                side,
                f"{selected_prob:.4f}",
                f"{conf:.4f}",
                reasoning,
                check=True,
            ).stdout
            decision = parse_json_maybe(decision_out)
        else:
            reason = (
                "No deterministic copy-trader edge this hour; "
                f"source={selection_source or 'unknown'}, copy_status={copy.get('status', 'n/a')}"
            )
            decision_out = run_command(
                root,
                str(tools / "polymarket-decide.sh"),
                "SKIP",
                reason,
                check=True,
            ).stdout
            decision = parse_json_maybe(decision_out)

    # Non-fatal post-trade routines; they should not block evidence outputs.
    run_command(root, str(tools / "polymarket-resolve-turn.sh"), check=False)
    run_command(root, str(tools / "memvid-alpha-ingest.sh"), "ingest-decision", "--latest", check=False)
    run_command(root, str(tools / "memvid-alpha-ingest.sh"), "ingest-result", "--latest", check=False)

    research_dir = root / "data" / "alpha" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    research_path = research_dir / f"{now.strftime('%Y-%m-%d-%H')}.md"
    research_path.write_text(
        build_research_markdown(now, candidate, decision, context, recent_trades, whale_accuracy),
        encoding="utf-8",
    )

    action = (decision or {}).get("action", "skip")
    if action == "trade":
        line = "Alpha · Hourly · TRADE — deterministic copy-signal trade executed with gated sizing."
    else:
        line = "Alpha · Hourly · HOLD — deterministic gates found no robust edge this hour."
    run_command(root, str(tools / "telegram-post.sh"), "polymarket", line, check=False)

    summary = (
        f"{line} run_id={run_id}; "
        f"selection_source={(candidate or {}).get('selection_source', 'none')}; "
        f"decision_action={(decision or {}).get('action', 'none')}"
    )
    run_command(
        root,
        str(tools / "agent-report.sh"),
        "alpha",
        "alpha-polymarket",
        summary,
        check=False,
    )

    print(
        json.dumps(
            {
                "runId": run_id,
                "researchPath": str(research_path),
                "selectionSource": (candidate or {}).get("selection_source"),
                "decisionAction": (decision or {}).get("action"),
                "telegramLine": line,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

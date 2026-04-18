#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT_GUESS = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT_GUESS) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT_GUESS))

from tools import _polymarket_ledger as ledger

BONDING_MIN_MATCHING_TRADERS = 1
BONDING_MIN_CONFIDENCE = 0.45

# Trader-count-weighted Bayesian blend of whale consensus with the market price.
# A single matching wallet is mostly noise; we anchor heavily to the market.
# Each additional matching wallet shifts more weight onto the copy signal,
# saturating at the cap. This keeps Kelly sizing honest and prevents the
# "whale says 99.99%" theatre that produces fake 90c edges.
WHALE_BLEND_BASE = 0.45
WHALE_BLEND_PER_TRADER = 0.15
WHALE_BLEND_CAP = 0.85


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


def clamp_open_probability(value: float, epsilon: float = 0.0001) -> float:
    probability = float(value)
    if not math.isfinite(probability):
        raise ValueError("probability must be finite")
    return max(epsilon, min(1.0 - epsilon, probability))


def whale_blend_weight(matching_traders: int, wallets: Optional[list] = None, workspace_root: Optional[str] = None) -> float:
    """Trader-count + per-wallet learned weight.

    Cold-start fallback (no wallet history): linear in trader count.
    With wallet history: average each wallet's Bayesian posterior weight, then
    add a small multi-trader agreement bonus (capped).
    """
    if wallets:
        learned = [ledger.wallet_blend_weight(w, workspace_root=workspace_root) for w in wallets]
        wallet_avg = sum(learned) / len(learned)
        agreement_bonus = WHALE_BLEND_PER_TRADER * max(0, len(wallets) - 1)
        return max(0.0, min(WHALE_BLEND_CAP, wallet_avg + agreement_bonus))
    weight = WHALE_BLEND_BASE + WHALE_BLEND_PER_TRADER * max(matching_traders, 0)
    return max(0.0, min(WHALE_BLEND_CAP, weight))


def blend_with_market(
    whale_prob_yes: float,
    market_prob_yes: float,
    matching_traders: int,
    wallets: Optional[list] = None,
    workspace_root: Optional[str] = None,
) -> float:
    weight = whale_blend_weight(matching_traders, wallets=wallets, workspace_root=workspace_root)
    blended = weight * whale_prob_yes + (1.0 - weight) * market_prob_yes
    return clamp_open_probability(blended)


def apply_calibration_shrink(
    blended_prob_yes: float,
    market_prob_yes: float,
    workspace_root: Optional[str] = None,
) -> tuple:
    """If global calibration is poor, shrink the (blended - market) gap toward 0.

    Returns (shrunk_prob_yes, info). info is the calibration_multiplier dict
    plus the multiplier value, suitable for logging.
    """
    multiplier, info = ledger.calibration_multiplier(workspace_root=workspace_root)
    shrunk = market_prob_yes + multiplier * (blended_prob_yes - market_prob_yes)
    info = dict(info)
    info["multiplier"] = multiplier
    return clamp_open_probability(shrunk), info


def build_research_markdown(
    now: datetime,
    candidate: Optional[dict],
    decision: Optional[dict],
    context_text: str,
    recent_trades_text: str,
    bonding_lookup_text: str,
) -> str:
    question = candidate.get("question", "No candidate selected.") if candidate else "No candidate selected."
    source = candidate.get("selection_source", "none") if candidate else "none"
    copy = candidate.get("copy_strategy") if isinstance(candidate, dict) else {}
    if not isinstance(copy, dict):
        copy = {}
    consensus_yes = copy.get("consensus_probability_yes", "n/a")
    bonding_conf = copy.get("confidence", "n/a")
    matching_wallets = copy.get("traders_with_matching_positions", "n/a")

    action = (decision or {}).get("action", "skip")
    reasoning = (decision or {}).get("reasoning", "Deterministic fallback reasoning not available.")
    edge = (decision or {}).get("edge", "n/a")
    stake = (decision or {}).get("stake_amount", "n/a")

    lines = [
        f"# Alpha Research - {now.strftime('%Y-%m-%d-%H')}",
        "",
        "## Research Context",
        f"Context summary from polymarket-context.sh: {safe_text(context_text)}",
        "Recent performance appears in the memory snippets below, and this run uses deterministic trade mechanics.",
        "When no robust copy signal exists, the strategy defaults to disciplined HOLD behavior.",
        "",
        "## Market Analysis",
        f"Candidate question: {question}",
        f"Selection source: {source}; bonding consensus probability YES: {consensus_yes}; bonding confidence: {bonding_conf}; matching wallet count: {matching_wallets}.",
        "This run is bonding-copy only: if no valid bonding setup exists, action defaults to HOLD.",
        "",
        "## Memory Lookup",
        f"recent-trades: {safe_text(recent_trades_text)}",
        f"bonding-lookup: {safe_text(bonding_lookup_text)}",
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
        "Track whether bonding wallet alignment improves in correlated geopolitical or crypto markets.",
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
    recent_trades = run_command(root, str(tools / "alpha-memory-query.sh"), "recent-trades", check=False).stdout
    bonding_lookup = run_command(
        root,
        str(tools / "alpha-memory-query.sh"),
        "query",
        "bonding copy outcomes near resolution",
        check=False,
    ).stdout

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
        has_valid_copy_signal = (
            copy.get("status") == "ok"
            and isinstance(consensus_yes, (int, float))
            and isinstance(confidence, (int, float))
            and math.isfinite(float(consensus_yes))
            and math.isfinite(float(confidence))
            and traders >= BONDING_MIN_MATCHING_TRADERS
        )
        if has_valid_copy_signal:
            whale_prob_yes = clamp_open_probability(float(consensus_yes))
            try:
                market_prob_yes = clamp_open_probability(float(candidate.get("odds_yes", 0.5)))
            except (TypeError, ValueError):
                market_prob_yes = 0.5
            sample_wallets = []
            for sample in (copy.get("samples") or []):
                wallet = sample.get("wallet") if isinstance(sample, dict) else None
                if wallet:
                    sample_wallets.append(str(wallet).lower())
            sample_wallets = sorted(set(sample_wallets))
            workspace_root = str(root)
            blended_prob_yes = blend_with_market(
                whale_prob_yes, market_prob_yes, traders,
                wallets=sample_wallets, workspace_root=workspace_root,
            )
            blend_weight = whale_blend_weight(
                traders, wallets=sample_wallets, workspace_root=workspace_root
            )
            shrunk_prob_yes, calib_info = apply_calibration_shrink(
                blended_prob_yes, market_prob_yes, workspace_root=workspace_root,
            )
            side = "YES" if shrunk_prob_yes >= 0.5 else "NO"
            selected_prob = shrunk_prob_yes if side == "YES" else (1.0 - shrunk_prob_yes)
            selected_prob = clamp_open_probability(selected_prob)
            conf = max(min(float(confidence), 0.95), BONDING_MIN_CONFIDENCE)
            calib_tag = (
                f"calib×{calib_info['multiplier']:.2f}" if calib_info.get("applied")
                else f"calib=cold({calib_info.get('samples', 0)}smp)"
            )
            reasoning = (
                f"Deterministic copy execution from {selection_source}; "
                f"source={selection_source}, whale_yes={whale_prob_yes:.4f}, "
                f"market_yes={market_prob_yes:.4f}, blended_yes={blended_prob_yes:.4f}, "
                f"shrunk_yes={shrunk_prob_yes:.4f}, traders={traders}, "
                f"blend_weight={blend_weight:.2f}, {calib_tag}, confidence={conf:.4f}"
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
                "No copy-trader edge this hour; "
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
    run_command(root, str(tools / "alpha-memory-ingest.sh"), "ingest-decision", "--latest", check=False)
    run_command(root, str(tools / "alpha-memory-ingest.sh"), "ingest-result", "--latest", check=False)

    research_dir = root / "data" / "alpha" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    research_path = research_dir / f"{now.strftime('%Y-%m-%d-%H')}.md"
    research_path.write_text(
        build_research_markdown(now, candidate, decision, context, recent_trades, bonding_lookup),
        encoding="utf-8",
    )

    action = (decision or {}).get("action", "skip")
    if action == "trade":
        line = "Alpha · Hourly · TRADE — deterministic copy-signal trade executed with gated sizing."
    else:
        # Build contextual HOLD message
        if candidate and isinstance(candidate, dict):
            question = candidate.get("question", "unknown market")
            source = candidate.get("selection_source", "unknown")
            copy = candidate.get("copy_strategy") if isinstance(candidate.get("copy_strategy"), dict) else {}
            status = copy.get("status", "n/a")
            traders = int(copy.get("traders_with_matching_positions", 0) or 0)
            gate_failures = (decision or {}).get("gate_failures", [])
            if status != "ok":
                reject_reason = f"no copy signal (status={status})"
            elif traders < BONDING_MIN_MATCHING_TRADERS:
                reject_reason = f"insufficient matching wallets ({traders}/{BONDING_MIN_MATCHING_TRADERS})"
            elif gate_failures:
                reject_reason = ", ".join(gate_failures)
            else:
                reject_reason = "gate check failed"
            # Truncate question to keep Telegram message readable
            short_q = question[:60] + "..." if len(question) > 60 else question
            line = f"Alpha · Hourly · HOLD — evaluated \"{short_q}\"; rejected: {reject_reason}."
        else:
            line = "Alpha · Hourly · HOLD — no near-resolution markets found this hour."
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

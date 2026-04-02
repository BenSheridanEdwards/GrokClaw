#!/usr/bin/env python3
"""Summarize Telegram audit logs and flag low-clarity patterns."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path


OUTBOUND_SENT_KINDS = {"telegram_post", "telegram_inline"}
OUTBOUND_FAILED_KINDS = {"telegram_post_failed", "telegram_inline_failed"}
INBOUND_KINDS = {"telegram_incoming"}


def workspace_root() -> Path:
    return Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[1]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Telegram audit report from data/audit-log/*.jsonl"
    )
    parser.add_argument(
        "--date",
        default=dt.datetime.utcnow().strftime("%Y-%m-%d"),
        help="Anchor UTC date in YYYY-MM-DD format (default: today UTC)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of days ending at --date to include (default: 1)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Max number of clarity flags and recent messages to print (default: 10)",
    )
    return parser.parse_args()


def date_window(anchor: dt.date, days: int) -> tuple[dt.date, list[dt.date]]:
    if days < 1:
        days = 1
    start = anchor - dt.timedelta(days=days - 1)
    dates = [start + dt.timedelta(days=index) for index in range(days)]
    return start, dates


def read_events(root: Path, dates: list[dt.date]) -> list[dict]:
    directory = root / "data" / "audit-log"
    events: list[dict] = []
    for day in dates:
        path = directory / f"{day.strftime('%Y-%m-%d')}.jsonl"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                events.append(payload)
    return events


def reasons_for_event(event: dict) -> list[str]:
    kind = str(event.get("kind", ""))
    message = str(event.get("message", "")).strip()
    topic_id = str(event.get("topicId", "")).strip()
    reasons: list[str] = []

    if kind in OUTBOUND_SENT_KINDS | OUTBOUND_FAILED_KINDS:
        if len(message) < 12:
            reasons.append("too_short")
        if re.search(r"<[^>]+>", message):
            reasons.append("unresolved_placeholder")
        if len(message) > 80 and "\n" not in message:
            reasons.append("long_no_structure")
        if len(message) > 32 and not re.search(r"[.!?]$", message):
            reasons.append("missing_terminal_punctuation")

    if kind in INBOUND_KINDS and ":" not in topic_id:
        reasons.append("invalid_action_token")

    return reasons


def sort_key(event: dict) -> str:
    return str(event.get("ts", ""))


def one_line(text: str) -> str:
    return " ".join(text.strip().split())


def suggest_improvement(event: dict, reasons: list[str]) -> str:
    kind = str(event.get("kind", ""))
    topic = str(event.get("topic", ""))
    message = str(event.get("message", "")).strip()

    if "invalid_action_token" in reasons:
        return "Use 'Label | action:id' format, e.g. 'Approve | approve_suggestion:12'."

    improved = message
    if "unresolved_placeholder" in reasons:
        improved = re.sub(r"<[^>]+>", "[fill value]", improved)
    if "missing_terminal_punctuation" in reasons and improved and not re.search(r"[.!?]$", improved):
        improved = improved + "."
    if "too_short" in reasons:
        if topic == "suggestions":
            return "Daily suggestion: <clear title>. Why it matters: <reason>. Next step: <action>."
        if topic == "health":
            return "Health alert: <what failed>. Impact: <impact>. Next step: <owner action>."
        return "Update: <what happened>. Why it matters: <impact>. Next step: <action>."
    if "long_no_structure" in reasons:
        return "Split into 2-3 short lines: headline, reason, next step."

    if improved != message:
        return improved
    return "Rewrite for clarity: explicit subject, impact, and next step."


def render_report(
    events: list[dict], anchor: dt.date, start: dt.date, days: int, limit: int
) -> str:
    total = len(events)
    inbound = sum(1 for event in events if event.get("kind") in INBOUND_KINDS)
    outbound_sent = sum(1 for event in events if event.get("kind") in OUTBOUND_SENT_KINDS)
    outbound_failed = sum(
        1 for event in events if event.get("kind") in OUTBOUND_FAILED_KINDS
    )

    topic_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    flagged: list[tuple[dict, list[str]]] = []

    for event in events:
        topic = str(event.get("topic", "unknown"))
        kind = str(event.get("kind", "unknown"))
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        kind_counts[kind] = kind_counts.get(kind, 0) + 1

        reasons = reasons_for_event(event)
        if reasons:
            flagged.append((event, reasons))

    lines = [
        "Telegram Audit Report (UTC)",
        f"Window: {start.strftime('%Y-%m-%d')} -> {anchor.strftime('%Y-%m-%d')} ({days} day{'s' if days != 1 else ''})",
        f"Total events: {total}",
        f"Inbound actions: {inbound}",
        f"Outbound sent: {outbound_sent}",
        f"Outbound failed: {outbound_failed}",
        "",
        "By kind:",
    ]
    if kind_counts:
        for kind in sorted(kind_counts):
            lines.append(f"- {kind}: {kind_counts[kind]}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("By topic:")
    if topic_counts:
        for topic in sorted(topic_counts):
            lines.append(f"- {topic}: {topic_counts[topic]}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Clarity flags:")
    if flagged:
        for event, reasons in sorted(flagged, key=lambda item: sort_key(item[0]), reverse=True)[:limit]:
            bad_message = one_line(str(event.get("message", "")))
            suggestion = suggest_improvement(event, reasons)
            lines.append(
                f"- [{event.get('kind','unknown')}] topic={event.get('topic','unknown')} "
                f"reasons={','.join(reasons)} bad_message={bad_message} "
                f"improve_to={one_line(suggestion)}"
            )
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Recent messages:")
    if events:
        for event in sorted(events, key=sort_key, reverse=True)[:limit]:
            lines.append(
                f"- {event.get('ts','')} [{event.get('kind','unknown')}/{event.get('topic','unknown')}] "
                f"{str(event.get('message','')).strip()}"
            )
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    try:
        anchor = dt.datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print("invalid --date (expected YYYY-MM-DD)")
        return 1

    start, dates = date_window(anchor, args.days)
    events = read_events(workspace_root(), dates)
    report = render_report(events, anchor, start, max(1, args.days), max(1, args.limit))
    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

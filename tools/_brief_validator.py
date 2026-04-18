#!/usr/bin/env python3
"""Post-hoc validator for the Grok daily brief.

Catches the specific failure mode where the LLM invents GitHub repos that do
not appear in that day's github-discover JSON. It parses the brief markdown,
extracts every bolded or header-level owner/repo mention, and reports any
that are not in the classified discovery set.

Usage:
  python3 tools/_brief_validator.py --date 2026-04-18 [--workspace .]

Exit codes:
  0 — OK (no hallucinations, both files present)
  1 — discovery JSON missing
  2 — brief markdown missing
  3 — hallucinations detected

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

# Bolded inline mention: **owner/repo** — the canonical discovery format.
BOLD_SLUG_RE = re.compile(r"\*\*([A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*)\*\*")
# Markdown header slug: lines starting with #{1,6} followed by owner/repo.
HEADER_SLUG_RE = re.compile(
    r"(?m)^\s{0,3}#{1,6}\s+([A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*)\b"
)

DEFAULT_WHITELIST = frozenset({
    # Ben's own repo(s) are legitimate mentions not surfaced by discovery.
    "bensheridanedwards/grokclaw",
})


@dataclass
class ValidationResult:
    ok: bool
    hallucinated: set = field(default_factory=set)
    mentioned: set = field(default_factory=set)
    discovered: set = field(default_factory=set)
    errors: list = field(default_factory=list)


def extract_repo_mentions(markdown: str) -> set:
    out: set = set()
    for m in BOLD_SLUG_RE.finditer(markdown):
        out.add(m.group(1))
    for m in HEADER_SLUG_RE.finditer(markdown):
        out.add(m.group(1))
    return out


def _load_discovery_repos(path: Path) -> Optional[set]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    names: set = set()
    for key in ("starred", "trending"):
        for repo in data.get(key) or []:
            name = (repo.get("name") or "").strip()
            if name:
                names.add(name.lower())
    return names


def validate_brief(
    workspace_root: str,
    date: str,
    whitelist: Optional[Iterable[str]] = None,
) -> ValidationResult:
    root = Path(workspace_root)
    brief_path = root / "data" / "briefs" / f"{date}.md"
    discovery_path = root / "data" / "github-discover" / f"{date}.json"

    result = ValidationResult(ok=True)
    discovered = _load_discovery_repos(discovery_path)
    if discovered is None:
        result.ok = False
        result.errors.append("discovery_missing")
    else:
        result.discovered = discovered

    if not brief_path.exists():
        result.ok = False
        result.errors.append("brief_missing")
        return result

    markdown = brief_path.read_text(encoding="utf-8")
    mentioned_raw = extract_repo_mentions(markdown)
    mentioned = {m.lower() for m in mentioned_raw}
    result.mentioned = mentioned

    wl = {w.lower() for w in (whitelist or DEFAULT_WHITELIST)}
    if discovered is not None:
        hallucinated = mentioned - discovered - wl
        result.hallucinated = hallucinated
        if hallucinated:
            result.ok = False
            result.errors.append("hallucinated_repos")

    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_ws = os.environ.get("WORKSPACE_ROOT") or str(Path(__file__).resolve().parents[1])
    parser.add_argument("--workspace", default=default_ws)
    parser.add_argument("--date", default=datetime.utcnow().strftime("%Y-%m-%d"))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv[1:])

    result = validate_brief(args.workspace, args.date)

    if not args.quiet:
        if "discovery_missing" in result.errors:
            print(f"FAIL: discovery JSON missing for {args.date}", file=sys.stderr)
        if "brief_missing" in result.errors:
            print(f"FAIL: brief markdown missing for {args.date}", file=sys.stderr)
        if result.hallucinated:
            print(
                "FAIL: brief mentions repos not in discovery: "
                + ", ".join(sorted(result.hallucinated)),
                file=sys.stderr,
            )
        if result.ok:
            print(f"OK: brief {args.date} validated ({len(result.mentioned)} repos)")

    if "discovery_missing" in result.errors:
        return 1
    if "brief_missing" in result.errors:
        return 2
    if result.hallucinated:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

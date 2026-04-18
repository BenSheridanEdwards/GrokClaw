#!/usr/bin/env python3
"""Pre-render the DISCOVERED section of the Grok daily brief.

The LLM has repeatedly hallucinated repo names from in-prompt examples into
the brief instead of parsing the discovery JSON. This tool removes that
failure mode by producing a deterministic markdown block the prompt treats
as authoritative: the LLM may only add analysis paragraphs under each repo.

Classification:
  - IN_STACK: repo owner/slug or bare repo name already appears in a
    known stack reference (MEMORY.md, NorthStar.md, AGENTS.md, README.md,
    docs/prompts/*.md, graphify-out/wiki/*.md).
  - NEW: otherwise.

The tool also flags repos that appeared in briefs written in the last N days
as SEEN_RECENTLY so Grok can suppress them from the Telegram DISCOVERED
summary (they still appear in the companion research file).

Stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date as _date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional

STACK_REFERENCE_FILES = (
    "memory/MEMORY.md",
    "NorthStar.md",
    "AGENTS.md",
    "README.md",
    "CLAUDE.md",
    "TOOLS.md",
    "IDENTITY.md",
)
STACK_REFERENCE_GLOBS = (
    "docs/prompts/*.md",
    "graphify-out/wiki/*.md",
)

# Words that appear in repo names but carry zero signal as stack identifiers.
_NAME_STOPWORDS = frozenset({
    "test", "tests", "app", "api", "web", "ui", "ai", "ml", "cli", "js",
    "ts", "py", "go", "rs", "core", "lib", "utils", "tool", "tools",
    "main", "src", "demo", "example", "examples", "common", "server",
    "client", "data", "docs", "doc", "readme",
})

SLUG_RE = re.compile(r"\b([A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*)\b")


def load_discovery(workspace_root: str, date: str) -> Optional[dict]:
    path = Path(workspace_root) / "data" / "github-discover" / f"{date}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _collect_reference_text(workspace_root: str) -> str:
    root = Path(workspace_root)
    chunks: list[str] = []
    for rel in STACK_REFERENCE_FILES:
        p = root / rel
        if p.exists():
            chunks.append(_read_text(p))
    for pattern in STACK_REFERENCE_GLOBS:
        for p in sorted(root.glob(pattern)):
            chunks.append(_read_text(p))
    return "\n".join(chunks)


def load_stack_index(workspace_root: str) -> dict:
    """Return {'slugs': set[str], 'names': set[str]} for cross-reference lookup."""
    text = _collect_reference_text(workspace_root)
    slugs = {m.group(1).lower() for m in SLUG_RE.finditer(text)}
    names: set[str] = set()
    for slug in slugs:
        tail = slug.split("/", 1)[1] if "/" in slug else slug
        if tail and tail not in _NAME_STOPWORDS:
            names.add(tail)
    # Also harvest explicitly-mentioned tool names: simple heuristic picks
    # any backticked or single-word lowercase token we know is a tool by
    # scanning the text — we deliberately keep this conservative and only
    # pick tokens that look like repo names.
    lowered = text.lower()
    for candidate in {
        "graphify", "mempalace", "autoresearch", "paperclip", "telegram",
        "openclaw", "ollama", "linear", "cursor",
    }:
        if candidate in lowered:
            names.add(candidate)
    return {"slugs": slugs, "names": names}


def classify_repo(repo: dict, stack_index: dict) -> str:
    slug = str(repo.get("name") or "").lower()
    if not slug:
        return "NEW"
    if slug in stack_index.get("slugs", set()):
        return "IN_STACK"
    tail = slug.split("/", 1)[1] if "/" in slug else slug
    if tail and tail in _NAME_STOPWORDS:
        return "NEW"
    if tail and tail in stack_index.get("names", set()):
        return "IN_STACK"
    return "NEW"


def _parse_date(s: str) -> Optional[_date]:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def recently_surfaced(
    repo_name: str, workspace_root: str, today: Optional[str] = None, days: int = 7,
) -> bool:
    briefs_dir = Path(workspace_root) / "data" / "briefs"
    if not briefs_dir.exists():
        return False
    today_d = _parse_date(today) if today else datetime.utcnow().date()
    if today_d is None:
        return False
    cutoff = today_d - timedelta(days=days)
    needle = repo_name.lower()
    for path in sorted(briefs_dir.glob("*.md")):
        stem = path.stem
        d = _parse_date(stem)
        if d is None:
            continue
        if d < cutoff or d >= today_d:
            continue
        if needle in _read_text(path).lower():
            return True
    return False


def _repo_line(repo: dict, label: str, seen: bool) -> str:
    name = repo.get("name") or "unknown"
    stars = repo.get("stars") or 0
    lang = repo.get("language") or "—"
    desc = (repo.get("description") or "").strip() or "(no description)"
    url = repo.get("url") or ""
    flags = [label]
    if seen:
        flags.append("SEEN_RECENTLY")
    flag_str = " · ".join(flags)
    return (
        f"- **{name}** ({stars} stars, {lang}) — [{flag_str}]\n"
        f"  Description: {desc}\n"
        f"  URL: {url}\n"
    )


def render_block(workspace_root: str, date: str) -> str:
    data = load_discovery(workspace_root, date)
    if data is None:
        return (
            "Discovery file not found for "
            f"{date} — run ./tools/github-discover.sh\n"
        )
    stack = load_stack_index(workspace_root)
    starred = data.get("starred") or []
    trending = data.get("trending") or []
    lines: list[str] = []
    lines.append(f"# Authoritative discovery block — {date}\n")
    lines.append(
        "This block is generated from "
        f"data/github-discover/{date}.json and is authoritative. "
        "Do not add, remove, or rename repos. Add a 3-6 sentence analysis "
        "paragraph under each entry.\n"
    )
    lines.append("## Starred (last 7 days)\n")
    if not starred:
        lines.append("(none)\n")
    for repo in starred:
        label = classify_repo(repo, stack)
        seen = recently_surfaced(repo.get("name") or "", workspace_root, today=date)
        lines.append(_repo_line(repo, label, seen))
    lines.append("\n## Trending (last 7 days)\n")
    if not trending:
        lines.append("(none)\n")
    for repo in trending:
        label = classify_repo(repo, stack)
        seen = recently_surfaced(repo.get("name") or "", workspace_root, today=date)
        lines.append(_repo_line(repo, label, seen))
    return "".join(lines)


def main(argv: Iterable[str]) -> int:
    args = list(argv)
    workspace_root = os.environ.get("WORKSPACE_ROOT") or str(Path(__file__).resolve().parents[1])
    date = args[1] if len(args) > 1 else datetime.utcnow().strftime("%Y-%m-%d")
    sys.stdout.write(render_block(workspace_root, date))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

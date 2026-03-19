#!/bin/sh
# Append a lessons-learned bullet to memory/MEMORY.md after PR review.
# Used by Grok in the self-improvement loop: after approving a PR, Grok reviews
# accuracy (did implementation match spec? was estimate right?) and runs this.
#
# Usage: append-lesson-learned.sh <issue-id> "<lesson text>"
# Example: append-lesson-learned.sh GRO-17 "Implementation matched spec. Ticket clarity helped."
#
# Run by: Grok as part of PR review workflow (AGENTS.md step 6).
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
MEMORY_PATH="$WORKSPACE_ROOT/memory/MEMORY.md"

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <issue-id> \"<lesson text>\"" >&2
  exit 1
fi

ISSUE_ID="$1"
LESSON="$2"
TODAY=$(date -u +%Y-%m-%d)

if [ ! -f "$MEMORY_PATH" ]; then
  echo "MEMORY.md not found at $MEMORY_PATH" >&2
  exit 1
fi

python3 - "$MEMORY_PATH" "$TODAY" "$ISSUE_ID" "$LESSON" <<'PY'
import pathlib
import sys

memory_path = pathlib.Path(sys.argv[1])
today = sys.argv[2]
issue_id = sys.argv[3]
lesson = sys.argv[4]
section_header = "## Lessons learned"
entry = f"- **{today}** — {issue_id}: {lesson}"

content = memory_path.read_text(encoding="utf-8")
if section_header not in content:
    content = content.rstrip() + f"\n\n---\n\n{section_header}\n\n{entry}\n"
else:
    marker = f"{section_header}\n\n"
    content = content.replace(marker, f"{marker}{entry}\n", 1)

memory_path.write_text(content, encoding="utf-8")
PY

echo "Appended lesson for $ISSUE_ID to memory/MEMORY.md"

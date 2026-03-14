#!/bin/sh
# Polymarket digest: aggregate past 7 days, post Slack digest, append to MEMORY.md.
# Usage: polymarket-digest.sh
# Run via cron (agent_turn) every Monday at 01:00 UTC.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${PICOCLAW_WORKSPACE:-$(cd "$SCRIPT_DIR/.." && pwd)}"

OUTPUT=$(python3 "$SCRIPT_DIR/_polymarket_digest.py" "$WORKSPACE_ROOT")

PAYLOAD="${OUTPUT#DIGEST_JSON:}"
SLACK_MSG=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["slack_msg"])' "$PAYLOAD")
IMPROVEMENT=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["improvement"])' "$PAYLOAD")

SLACK_CHANNEL="${SLACK_CHANNEL_ID:-C0ALE1S0LSF}"

if [ -n "$SLACK_MSG" ]; then
  "$WORKSPACE_ROOT/tools/slack-post.sh" "$SLACK_CHANNEL" "$SLACK_MSG" || true
fi

MEMORY_PATH="$WORKSPACE_ROOT/memory/MEMORY.md"

if [ -n "$IMPROVEMENT" ] && [ -f "$MEMORY_PATH" ]; then
  TODAY=$(date -u +%Y-%m-%d)
  python3 - "$MEMORY_PATH" "$TODAY" "$IMPROVEMENT" <<'PY'
import pathlib
import sys

memory_path = pathlib.Path(sys.argv[1])
today = sys.argv[2]
improvement = sys.argv[3]
section_header = "## Polymarket calibration notes"
entry = f"- **{today}** — {improvement}"

content = memory_path.read_text(encoding="utf-8")
if section_header not in content:
    content = content.rstrip() + f"\n\n---\n\n{section_header}\n\n{entry}\n"
else:
    marker = f"{section_header}\n\n"
    content = content.replace(marker, f"{marker}{entry}\n", 1)

memory_path.write_text(content, encoding="utf-8")
PY
fi

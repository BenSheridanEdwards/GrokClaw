#!/bin/sh
# Polymarket digest: aggregate past 7 days, post Slack digest, append to MEMORY.md.
# Usage: polymarket-digest.sh
# Run via cron (agent_turn) every Monday at 01:00 UTC.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${PICOCLAW_WORKSPACE:-$(cd "$SCRIPT_DIR/.." && pwd)}"

# Load .env for Slack
if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

OUTPUT=$(python3 "$SCRIPT_DIR/_polymarket_digest.py" "$WORKSPACE_ROOT")

SLACK_MSG=""
IMPROVEMENT=""
MEMORY_PATH=""

while IFS= read -r line; do
  case "$line" in
    SLACK_MSG:*) SLACK_MSG="${line#SLACK_MSG:}" ;;
    IMPROVEMENT:*) IMPROVEMENT="${line#IMPROVEMENT:}" ;;
    MEMORY_PATH:*) MEMORY_PATH="${line#MEMORY_PATH:}" ;;
  esac
done <<EOF
$OUTPUT
EOF

SLACK_CHANNEL="${SLACK_CHANNEL_ID:-C0ALE1S0LSF}"

if [ -n "$SLACK_MSG" ]; then
  "$WORKSPACE_ROOT/tools/slack-post.sh" "$SLACK_CHANNEL" "$SLACK_MSG" || true
fi

if [ -n "$IMPROVEMENT" ] && [ -n "$MEMORY_PATH" ] && [ -f "$MEMORY_PATH" ]; then
  TODAY=$(date -u +%Y-%m-%d)
  echo "" >> "$MEMORY_PATH"
  echo "- **$TODAY** — $IMPROVEMENT" >> "$MEMORY_PATH"
fi

#!/bin/sh
# Output today's agent reports for Grok to synthesize.
# Grok runs this, reads the output, and posts a consolidated brief to the user.
#
# Usage: grok-daily-brief.sh [date]
#   date: YYYY-MM-DD (default: today)
#
# Cron: 0 8 * * * (8am daily, after Kimi 7am, Alpha 7:30am)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
REPORTS_DIR="$WORKSPACE_ROOT/data/agent-reports"
DATE="${1:-$(date +%Y-%m-%d)}"
FILE="$REPORTS_DIR/$DATE.json"

if [ ! -f "$FILE" ]; then
  echo "No agent reports for $DATE."
  exit 0
fi

echo "Agent reports for $DATE:"
echo "---"
cat "$FILE"

#!/bin/sh
# Install resilient local cron triggers for the Polymarket paper-trading loop.
# Usage: install-polymarket-cron.sh
set -eu

TMPFILE="$(mktemp)"
trap 'rm -f "$TMPFILE"' EXIT

crontab -l 2>/dev/null | python3 - <<'PY' > "$TMPFILE"
import sys

entries = [
    "30 23 * * * /Users/jarvis/.picoclaw/workspace/tools/polymarket-daily-turn.sh >> /tmp/polymarket-daily-turn.log 2>&1",
    "45 23 * * * /Users/jarvis/.picoclaw/workspace/tools/polymarket-resolve-turn.sh >> /tmp/polymarket-resolve.log 2>&1",
    "0 1 * * 1 /Users/jarvis/.picoclaw/workspace/tools/polymarket-digest.sh >> /tmp/polymarket-digest.log 2>&1",
]

current = [line.rstrip("\n") for line in sys.stdin]
filtered = [
    line
    for line in current
    if "polymarket-daily-turn.sh" not in line
    and "polymarket-resolve.sh" not in line
    and "polymarket-resolve-turn.sh" not in line
    and "polymarket-digest.sh" not in line
]

for line in filtered:
    print(line)
for entry in entries:
    print(entry)
PY

crontab "$TMPFILE"
crontab -l

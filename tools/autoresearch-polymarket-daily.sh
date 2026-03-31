#!/bin/sh
# Run discovery evolution (writes data/autoresearch-polymarket-strategy.json) and post Polymarket Telegram summary.
# Stdlib Python + telegram-post only; no remote exec.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
cd "$WORKSPACE_ROOT"

TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
if ! python3 skills/autoresearch-polymarket/evolve.py >"$TMP" 2>&1; then
  # Still try to post if we got a telegram line (e.g. partial success)
  :
fi
LINE=$(grep '^EVOLVED_TELEGRAM: ' "$TMP" | head -1 | sed 's/^EVOLVED_TELEGRAM: //' || true)
if [ -n "${LINE}" ]; then
  if ! "$WORKSPACE_ROOT/tools/telegram-post.sh" polymarket "${LINE}"; then
    echo "autoresearch-polymarket-daily: telegram delivery failed (missing TELEGRAM_* in .env?)" >&2
  fi
fi

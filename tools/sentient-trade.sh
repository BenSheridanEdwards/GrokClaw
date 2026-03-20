#!/bin/sh
# Sentient model-arena paper trade: fetch market or log prediction.
# Usage:
#   sentient-trade.sh
#     Fetches Manifold model-arena markets, stages candidate, prints JSON.
#   sentient-trade.sh <side> <reasoning>
#     Logs the staged candidate to data/sentient-trades.json.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ "$#" -eq 0 ]; then
  exec python3 "$SCRIPT_DIR/_sentient_trade.py" "$WORKSPACE_ROOT"
fi

if [ "$#" -eq 2 ]; then
  SIDE="$1"; shift
  REASONING="$1"
  exec python3 "$SCRIPT_DIR/_sentient_trade.py" "$WORKSPACE_ROOT" "$SIDE" "$REASONING"
fi

echo "usage: $0" >&2
echo "   or: $0 <side> <reasoning>" >&2
exit 1

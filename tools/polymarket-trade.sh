#!/bin/sh
# Polymarket paper trade: fetch top market or log Grok's prediction.
# Usage:
#   polymarket-trade.sh
#     Fetches markets, selects highest-volume closing within 7 days, stages the candidate, prints JSON.
#   polymarket-trade.sh <side> <reasoning>
#     Logs the staged candidate to data/polymarket-trades.json.
#   polymarket-trade.sh <market_id> <side> <odds> <reasoning> <question>
#     Logs trade to data/polymarket-trades.json.
# Run via cron (agent_turn) daily at 23:30 UTC.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ "$#" -eq 0 ]; then
  exec python3 "$SCRIPT_DIR/_polymarket_trade.py" "$WORKSPACE_ROOT"
fi

if [ "$#" -eq 2 ]; then
  SIDE="$1"; shift
  REASONING="$1"
  exec python3 "$SCRIPT_DIR/_polymarket_trade.py" \
    "$WORKSPACE_ROOT" "$SIDE" "$REASONING"
fi

if [ "$#" -ge 5 ]; then
  MARKET_ID="$1"; shift
  SIDE="$1"; shift
  ODDS="$1"; shift
  REASONING="$1"; shift
  QUESTION="$*"
  exec python3 "$SCRIPT_DIR/_polymarket_trade.py" \
    "$WORKSPACE_ROOT" "$MARKET_ID" "$SIDE" "$ODDS" "$REASONING" "$QUESTION"
fi

echo "usage: $0" >&2
echo "   or: $0 <side> <reasoning>" >&2
echo "   or: $0 <market_id> <side> <odds> <reasoning> <question>" >&2
exit 1

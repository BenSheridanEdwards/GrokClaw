#!/bin/sh
# Trigger the Grok Polymarket decision loop manually.
# Usage: polymarket-daily-turn.sh
set -eu

OPENCLAW_BIN="${OPENCLAW_BIN:-/opt/homebrew/bin/openclaw}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec "$OPENCLAW_BIN" agent \
  --session "cron:polymarket-daily-trade" \
  --message "Polymarket session (runs every 4h). Goal: make a bet every session. First read memory/MEMORY.md Polymarket section and run ./tools/polymarket-context.sh to load recent decisions and results. Use this to calibrate. Then run ./tools/polymarket-trade.sh to fetch and stage the candidate. Read copy_strategy from the output. Run web_search with at least 2 queries to validate. Prefer to trade: only SKIP when evidence strongly conflicts or no tradeable market exists. When there is a marginal edge, choose YES or NO with your best estimate. Run ./tools/polymarket-decide.sh <side> <probability> <confidence> \"<reasoning>\". After deciding, run ./tools/polymarket-report.sh. Then post to Telegram: ./tools/telegram-post.sh polymarket \"Session: [traded YES/NO on <question> | skipped: <reason>]. Why: [one sentence]. Bankroll: \$X, accuracy: Y%.\"" \
  --model grok-4.1-fast

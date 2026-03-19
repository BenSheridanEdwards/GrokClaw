#!/bin/sh
# Trigger the Grok Polymarket decision loop manually.
# Usage: polymarket-daily-turn.sh
set -eu

OPENCLAW_BIN="${OPENCLAW_BIN:-/opt/homebrew/bin/openclaw}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec "$OPENCLAW_BIN" agent \
  --session "cron:polymarket-daily-trade" \
  --message "Run ./tools/polymarket-trade.sh to fetch and stage today's candidate. Read the returned copy_strategy section (built from top Polymarket traders and their positions) and use it as a prior. Then run web_search with at least 2 queries for independent validation. If evidence conflicts or edge is unclear, run ./tools/polymarket-decide.sh SKIP \"<reason>\". Otherwise choose YES/NO with probability and confidence, then run ./tools/polymarket-decide.sh <side> <probability> <confidence> \"<one sentence reasoning mentioning copy_strategy + external evidence>\". After deciding, run ./tools/polymarket-report.sh and print final JSON." \
  --model grok-4.1-fast

#!/bin/sh
# Trigger the Grok Polymarket decision loop manually.
# Usage: polymarket-daily-turn.sh
set -eu

OPENCLAW_BIN="${OPENCLAW_BIN:-/opt/homebrew/bin/openclaw}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

# Load .env for TELEGRAM_* etc.; ensure gateway token for agent→gateway auth
if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi
# Always use GrokClaw config (port 18800, XAI); ignore OPENCLAW_CONFIG_PATH from env
CONFIG_PATH="$HOME/.openclaw/openclaw.json"
# Agent needs gateway token to connect; extract from config if not set
if [ -z "${OPENCLAW_GATEWAY_TOKEN:-}" ] && [ -f "$CONFIG_PATH" ]; then
  OPENCLAW_GATEWAY_TOKEN=$(node -p "try{require('$CONFIG_PATH').gateway.auth.token}catch(e){''}" 2>/dev/null) || true
  export OPENCLAW_GATEWAY_TOKEN
fi
# Force GrokClaw config so agent uses correct gateway URL/token (not OpenClawAgent)
export OPENCLAW_CONFIG_PATH="$CONFIG_PATH"
cd "$WORKSPACE_ROOT"
exec "$OPENCLAW_BIN" agent \
  --session-id "polymarket-$(date +%s)" \
  --message "Polymarket session (runs hourly). Goal: make a bet every session. First read memory/MEMORY.md Polymarket section and run ./tools/polymarket-context.sh to load recent decisions and results. Use this to calibrate. Loop until you place a bet or exhaust options: (1) Run ./tools/polymarket-trade.sh to fetch and stage the next candidate. If it returns no candidate, stop and post that to Telegram. (2) Read copy_strategy from the output. Run web_search with at least 2 queries to validate. (3) Prefer to trade: only SKIP when evidence strongly conflicts or no tradeable market exists. When there is a marginal edge, choose YES or NO with your best estimate. Run ./tools/polymarket-decide.sh <side> <probability> <confidence> \"<reasoning>\". (4) If you SKIP, go back to step 1 — the skipped market is excluded, so the next run returns a different whale-backed or volume candidate. Keep iterating through markets until you place a bet. After placing a bet (or exhausting options), run ./tools/polymarket-report.sh. Then post to Telegram: ./tools/telegram-post.sh polymarket \"Session: [traded YES/NO on <question> | no bet: <reason>]. Why: [one sentence]. Bankroll: \$X, accuracy: Y%.\""

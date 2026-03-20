#!/bin/sh
# Trigger the Sentient model-arena decision loop manually.
# Uses Kimi agent. Runs against Manifold model-arena markets (Grok vs Claude etc).
# Usage: sentient-daily-turn.sh
set -eu

OPENCLAW_BIN="${OPENCLAW_BIN:-openclaw}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi
CONFIG_PATH="${OPENCLAW_CONFIG_PATH:-$HOME/.openclaw/openclaw.json}"
if [ -z "${OPENCLAW_GATEWAY_TOKEN:-}" ] && [ -f "$CONFIG_PATH" ]; then
  OPENCLAW_GATEWAY_TOKEN=$(node -p "try{require('$CONFIG_PATH').gateway.auth.token}catch(e){''}" 2>/dev/null) || true
  export OPENCLAW_GATEWAY_TOKEN
fi
export OPENCLAW_CONFIG_PATH="${OPENCLAW_CONFIG_PATH:-$CONFIG_PATH}"
export OPENCLAW_AGENT_ID="${OPENCLAW_AGENT_ID:-kimi}"

cd "$WORKSPACE_ROOT"
MSG="Sentient model-arena session. Goal: bet when consensus predicts >5% shift. (1) Run ./tools/sentient-context.sh. (2) Run ./tools/sentient-trade.sh to fetch and stage a candidate (Grok vs Claude / model arena from Manifold). (3) Run web_search to validate. (4) Run ./tools/sentient-decide.sh <side> <probability> <confidence> \"<reasoning>\" or SKIP. (5) If SKIP, run sentient-trade.sh again for next market. (6) After trade or exhaust: ./tools/sentient-report.sh, then ./tools/telegram-post.sh sentient \"Session: [traded YES/NO on <q> | no bet]. Bankroll: \$X, accuracy: Y%.\" Run ./tools/agent-report.sh kimi sentient-daily-turn \"<summary>\"."
exec "$OPENCLAW_BIN" agent \
  --session-id "sentient-$(date +%s)" \
  --message "$MSG"

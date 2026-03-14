#!/bin/sh
# Trigger the Grok Polymarket decision loop without relying on PicoClaw cron persistence.
# Usage: polymarket-daily-turn.sh
set -eu

PICOCLAW_BIN="/Users/jarvis/.local/bin/picoclaw"
WORKSPACE_ROOT="/Users/jarvis/.picoclaw/workspace"

exec "$PICOCLAW_BIN" agent \
  --session "cron:polymarket-daily-trade" \
  --message "Use /Users/jarvis/.picoclaw/workspace as the workspace root. Run /Users/jarvis/.picoclaw/workspace/tools/polymarket-trade.sh to fetch and stage today's Polymarket candidate. Research the market using your web tools if needed. If you do not have a clear edge, run /Users/jarvis/.picoclaw/workspace/tools/polymarket-decide.sh SKIP \"<reason>\". If you do have an edge, choose YES or NO, estimate the probability for that chosen side as a decimal in (0,1), estimate confidence as a decimal in (0,1), and run /Users/jarvis/.picoclaw/workspace/tools/polymarket-decide.sh <side> <probability> <confidence> \"<one sentence reasoning>\". After the decision, run /Users/jarvis/.picoclaw/workspace/tools/polymarket-report.sh and print the final JSON report." \
  --model grok-4.1-fast

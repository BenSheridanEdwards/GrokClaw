#!/bin/sh
# E2E test: Fetch OpenClaw docs → snapshot → extract headings → post summary to Telegram.
#
# Usage: ./tools/browser-e2e-test.sh
#
# Requires: gateway running, browser enabled in ~/.openclaw/openclaw.json,
#           .env with Telegram credentials.
# Exit: 0 if agent run completes (success depends on browser tool availability).
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

SESSION_ID="browser-e2e-$(date +%s)"
MESSAGE="You are Grok. Run this E2E browser test:
1. Use the browser tool: action=start if needed, then action=snapshot with url=https://docs.openclaw.ai
2. From the snapshot content, extract all headings (h1, h2, h3)
3. Post a brief summary of the headings to Telegram: ./tools/telegram-post.sh suggestions \"Browser E2E: OpenClaw docs headings — <your summary>\""

cd "$WORKSPACE_ROOT"
exec openclaw agent --agent grok --message "$MESSAGE" --session-id "$SESSION_ID"

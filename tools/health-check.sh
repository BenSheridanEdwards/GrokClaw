#!/bin/sh
# Health check for PicoClaw gateway. Alerts to Slack if the gateway dies.
# Run via system cron, PicoClaw cron, or HEARTBEAT.
#
# Usage: health-check.sh
# Env:   PICOCLAW_WORKSPACE — workspace root (default: derived from script path)
#        SLACK_CHANNEL_ID   — Slack channel for alerts (default: C0ALE1S0LSF)
# Exit:  0 if healthy, 1 if unhealthy
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${PICOCLAW_WORKSPACE:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STATE_FILE="$WORKSPACE_ROOT/.gateway-health-state"
SLACK_CHANNEL="${SLACK_CHANNEL_ID:-C0ALE1S0LSF}"
GATEWAY_PORT="${PICOCLAW_GATEWAY_PORT:-18800}"

# Load .env for SLACK_BOT_TOKEN
if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

gateway_alive() {
  # Check if picoclaw gateway process is running
  if pgrep -f "picoclaw gateway" >/dev/null 2>&1; then
    return 0
  fi
  # Check gateway HTTP health endpoint
  if command -v curl >/dev/null 2>&1; then
    if curl -sf --connect-timeout 3 "http://127.0.0.1:${GATEWAY_PORT}/health" >/dev/null 2>&1; then
      return 0
    fi
  fi
  return 1
}

read_state() {
  [ -f "$STATE_FILE" ] && cat "$STATE_FILE" || echo "unknown"
}

write_state() {
  echo "$1" >"$STATE_FILE"
}

alert_slack() {
  "$WORKSPACE_ROOT/tools/slack-post.sh" "$SLACK_CHANNEL" \
    "🚨 GrokClaw gateway is down — restart required."
}

alive=$(gateway_alive && echo "alive" || echo "dead")
prev=$(read_state)

if [ "$alive" = "dead" ]; then
  if [ "$prev" != "dead" ]; then
    alert_slack
  fi
  write_state "dead"
  exit 1
fi

write_state "alive"
exit 0

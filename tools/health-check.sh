#!/bin/sh
# Health check for OpenClaw gateway. Alerts to Telegram if the gateway dies.
# Run via system cron, OpenClaw cron, or HEARTBEAT.
#
# Usage: health-check.sh
# Env:   WORKSPACE_ROOT — workspace root (default: derived from script path)
#        OPENCLAW_GATEWAY_PORT — gateway port (default: 18800)
# Exit:  0 if healthy, 1 if unhealthy
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STATE_FILE="$WORKSPACE_ROOT/.gateway-health-state"
GATEWAY_PORT="${OPENCLAW_GATEWAY_PORT:-18800}"

# Load .env for TELEGRAM_BOT_TOKEN
if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

# Single-poller guard: detect Telegram getUpdates conflicts and auto-disable
# legacy callback pollers. Non-fatal for health status.
"$WORKSPACE_ROOT/tools/telegram-poller-guard.sh" >/dev/null 2>&1 || true

gateway_alive() {
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

alert_telegram() {
  RETRY_DISABLE_ALERT=1 "$WORKSPACE_ROOT/tools/retry.sh" --max 3 --delay 1 --alert health -- \
    "$WORKSPACE_ROOT/tools/telegram-post.sh" health \
    "🚨 GrokClaw gateway is down — restart required."
}

alive=$(gateway_alive && echo "alive" || echo "dead")
prev=$(read_state)

if [ "$alive" = "dead" ]; then
  if [ "$prev" != "dead" ]; then
    alert_telegram
  fi
  "$WORKSPACE_ROOT/tools/grokclaw-doctor.sh" --heal --quiet 2>/dev/null || true
  if gateway_alive; then
    write_state "alive"
    exit 0
  fi
  write_state "dead"
  exit 1
fi

write_state "alive"
exit 0

#!/bin/sh
# External watchdog for OpenClaw gateway.
# - Runs a fast health probe
# - Attempts one restart if unhealthy
# - Posts Telegram alert on failure/recovery
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STATE_FILE="$WORKSPACE_ROOT/.gateway-watchdog-state"

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

GATEWAY_PORT="${OPENCLAW_GATEWAY_PORT:-18800}"

health_ok() {
  curl -sf --connect-timeout 3 "http://127.0.0.1:${GATEWAY_PORT}/health" >/dev/null 2>&1
}

read_state() {
  [ -f "$STATE_FILE" ] && cat "$STATE_FILE" || echo "unknown"
}

write_state() {
  printf '%s\n' "$1" >"$STATE_FILE"
}

if health_ok; then
  prev="$(read_state)"
  if [ "$prev" = "recovered" ] || [ "$prev" = "restart_failed" ]; then
    "$WORKSPACE_ROOT/tools/telegram-post.sh" health "Gateway watchdog: OpenClaw is healthy again." || true
  fi
  write_state "healthy"
  exit 0
fi

# Unhealthy: attempt one restart.
"$WORKSPACE_ROOT/tools/gateway-ctl.sh" restart >/dev/null 2>&1 || true
sleep 5

if health_ok; then
  write_state "recovered"
  "$WORKSPACE_ROOT/tools/telegram-post.sh" health "Gateway watchdog: restarted OpenClaw successfully after health failure." || true
  exit 0
fi

write_state "restart_failed"
"$WORKSPACE_ROOT/tools/telegram-post.sh" health "Gateway watchdog: auto-restart failed. Manual intervention required." || true
exit 1

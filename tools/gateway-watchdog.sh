#!/bin/sh
# External watchdog for OpenClaw gateway.
# - Owns gateway repair
# - Posts Telegram alert only when repair is exhausted or the gateway recovers after a reported failure
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STATE_FILE="$WORKSPACE_ROOT/.gateway-watchdog-state"
LOCK_DIR="$WORKSPACE_ROOT/.gateway-watchdog-lock"
MAX_ATTEMPTS="${GATEWAY_WATCHDOG_MAX_ATTEMPTS:-2}"
COOLDOWN_SECONDS="${GATEWAY_WATCHDOG_COOLDOWN_SECONDS:-240}"

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

if [ -x "$SCRIPT_DIR/gateway-port.sh" ]; then
  GATEWAY_PORT="$("$SCRIPT_DIR/gateway-port.sh")"
else
  GATEWAY_PORT="${OPENCLAW_GATEWAY_PORT:-18800}"
fi

health_ok() {
  command -v curl >/dev/null 2>&1 || return 1
  curl -sf --connect-timeout 3 "http://127.0.0.1:${GATEWAY_PORT}/health" >/dev/null 2>&1
}

load_state() {
  status="unknown"
  last_attempt="0"
  last_alert="0"
  if [ -f "$STATE_FILE" ]; then
    . "$STATE_FILE"
  fi
}

write_state() {
  cat >"$STATE_FILE" <<EOF
status=$1
last_attempt=$2
last_alert=$3
EOF
}

acquire_lock() {
  mkdir "$LOCK_DIR" 2>/dev/null
}

release_lock() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

now_epoch() {
  date -u +%s
}

attempt_repair() {
  "$WORKSPACE_ROOT/tools/gateway-ctl.sh" restart >/dev/null 2>&1 || true
  if [ -x "$WORKSPACE_ROOT/tools/sync-cron-jobs.sh" ]; then
    "$WORKSPACE_ROOT/tools/sync-cron-jobs.sh" >/dev/null 2>&1 || true
  fi
  if [ -x "$WORKSPACE_ROOT/tools/telegram-poller-guard.sh" ]; then
    "$WORKSPACE_ROOT/tools/telegram-poller-guard.sh" >/dev/null 2>&1 || true
  fi
}

send_failure_alert() {
  "$WORKSPACE_ROOT/tools/telegram-post.sh" health \
    "Gateway watchdog: OpenClaw is unhealthy after automatic repair attempts." || true
}

send_recovery_alert() {
  "$WORKSPACE_ROOT/tools/telegram-post.sh" health "Gateway watchdog: OpenClaw is healthy again." || true
}

load_state

if health_ok; then
  if [ "$status" = "repair_failed" ]; then
    send_recovery_alert
  fi
  write_state "healthy" "$last_attempt" "$last_alert"
  exit 0
fi

if ! acquire_lock; then
  exit 0
fi
trap release_lock EXIT INT TERM

current_epoch="$(now_epoch)"
if [ "$status" = "repair_failed" ] && [ $((current_epoch - last_attempt)) -lt "$COOLDOWN_SECONDS" ]; then
  exit 1
fi

attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  attempt_repair
  if health_ok; then
    write_state "healthy" "$current_epoch" "$last_alert"
    exit 0
  fi
  attempt=$((attempt + 1))
done

if [ $((current_epoch - last_alert)) -ge "$COOLDOWN_SECONDS" ]; then
  send_failure_alert
  last_alert="$current_epoch"
fi

write_state "repair_failed" "$current_epoch" "$last_alert"
exit 1

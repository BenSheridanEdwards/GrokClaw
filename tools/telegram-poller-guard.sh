#!/bin/sh
# Guardrail for Telegram single-poller mode.
# - Detects repeated getUpdates 409 conflicts in gateway logs
# - Disables legacy callback handler poller if present
# - Alerts to Telegram health topic (rate-limited)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STATE_DIR="${HOME}/.openclaw/state"
STATE_FILE="${STATE_DIR}/telegram-poller-guard.state"
LOG_FILE="${HOME}/.openclaw/logs/gateway-stderr.log"
WINDOW_SECS="${TELEGRAM_CONFLICT_WINDOW_SECS:-300}"
THRESHOLD="${TELEGRAM_CONFLICT_THRESHOLD:-3}"
ALERT_COOLDOWN_SECS="${TELEGRAM_CONFLICT_ALERT_COOLDOWN_SECS:-900}"
LABEL="com.grokclaw.callback-handler"

mkdir -p "$STATE_DIR"

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

[ -f "$STATE_FILE" ] || printf '0\n' >"$STATE_FILE"
last_alert_epoch="$(cat "$STATE_FILE" 2>/dev/null || echo 0)"

if [ ! -f "$LOG_FILE" ]; then
  exit 0
fi

conflicts="$(
python3 - "$LOG_FILE" "$WINDOW_SECS" <<'PY'
from datetime import datetime, timezone
import re
import sys

log_path = sys.argv[1]
window_secs = int(sys.argv[2])
now = datetime.now(timezone.utc)
count = 0
rx = re.compile(r"^(\d{4}-\d{2}-\d{2}T[^\s]+).+getUpdates conflict")

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        m = rx.search(line)
        if not m:
            continue
        ts = m.group(1)
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if (now - dt).total_seconds() <= window_secs:
            count += 1

print(count)
PY
)"

if [ "$conflicts" -lt "$THRESHOLD" ]; then
  exit 0
fi

# Auto-fix: disable any local callback poller service/process.
launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
pkill -f "telegram-callback-handler.py" 2>/dev/null || true

now_epoch="$(date +%s)"
since_last=$((now_epoch - last_alert_epoch))
if [ "$since_last" -ge "$ALERT_COOLDOWN_SECS" ]; then
  printf '%s\n' "$now_epoch" >"$STATE_FILE"
  "$WORKSPACE_ROOT/tools/telegram-post.sh" health \
    "⚠️ Telegram poller conflict detected (${conflicts}x in ${WINDOW_SECS}s). Auto-fix applied: disabled callback-handler poller. Keep a single getUpdates consumer active." \
    >/dev/null 2>&1 || true
fi

exit 0

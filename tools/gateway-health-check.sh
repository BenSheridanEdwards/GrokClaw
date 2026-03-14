#!/bin/sh
# Health check for PicoClaw gateway process. Alerts to Slack if the gateway dies.
# Run via system cron (e.g. */5 * * * *) — not via PicoClaw's agent cron, since
# the agent requires the gateway to be running.
#
# Usage: gateway-health-check.sh
# Env:   PICOCLAW_WORKSPACE — workspace root (default: derived from script path)
#        SLACK_CHANNEL_ID   — Slack channel for alerts (default: C0ALE1S0LSF)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${PICOCLAW_WORKSPACE:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STATE_FILE="$WORKSPACE_ROOT/.gateway-health-state"
SLACK_CHANNEL="${SLACK_CHANNEL_ID:-C0ALE1S0LSF}"

# Load .env for SLACK_BOT_TOKEN
if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

gateway_alive() {
  # Check if any picoclaw process is running (gateway is the main long-running process)
  if pgrep -f "picoclaw" >/dev/null 2>&1; then
    return 0
  fi
  # Optional: try HTTP health probe if gateway listens on default port
  if command -v curl >/dev/null 2>&1; then
    # Any response (including 404) means gateway is listening
    if curl -s --connect-timeout 3 -o /dev/null "http://127.0.0.1:18790/" 2>/dev/null; then
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
    "PicoClaw gateway process is not running. Check the server and restart with \`picoclaw gateway\`."
}

alive=$(gateway_alive && echo "alive" || echo "dead")
prev=$(read_state)

if [ "$alive" = "dead" ]; then
  if [ "$prev" != "dead" ]; then
    alert_slack
  fi
  write_state "dead"
else
  write_state "alive"
fi

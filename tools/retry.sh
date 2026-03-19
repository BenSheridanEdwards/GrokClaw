#!/bin/sh
# Retry a command with exponential backoff and optional Telegram alert.
# Usage:
#   retry.sh [--max N] [--delay S] [--alert TOPIC] -- <command...>
set -eu

MAX_ATTEMPTS=3
INITIAL_DELAY=2
ALERT_TOPIC="health"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --max)
      MAX_ATTEMPTS="$2"
      shift 2
      ;;
    --delay)
      INITIAL_DELAY="$2"
      shift 2
      ;;
    --alert)
      ALERT_TOPIC="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    *)
      echo "usage: retry.sh [--max N] [--delay S] [--alert TOPIC] -- <command...>" >&2
      exit 2
      ;;
  esac
done

if [ "$#" -eq 0 ]; then
  echo "retry.sh: missing command" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

attempt=1
delay="$INITIAL_DELAY"
last_exit=1

while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  if "$@"; then
    exit 0
  fi
  last_exit=$?

  if [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
    break
  fi

  # 0-20% jitter multiplier to avoid synchronized retries.
  jitter=$(awk 'BEGIN{srand(); printf "%.3f", 1 + (rand() * 0.2)}')
  sleep_for=$(awk -v d="$delay" -v j="$jitter" 'BEGIN{printf "%.3f", d*j}')
  sleep "$sleep_for"

  delay=$(awk -v d="$delay" 'BEGIN{printf "%.0f", d*2}')
  attempt=$((attempt + 1))
done

if [ "${RETRY_DISABLE_ALERT:-0}" != "1" ] && [ -x "$WORKSPACE_ROOT/tools/telegram-post.sh" ]; then
  cmd="$1"
  "$WORKSPACE_ROOT/tools/telegram-post.sh" "$ALERT_TOPIC" \
    "Retry failed after ${MAX_ATTEMPTS} attempts.
Command: ${cmd}
Exit code: ${last_exit}" >/dev/null 2>&1 || true
fi

exit "$last_exit"

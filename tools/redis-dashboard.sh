#!/bin/sh
# Redis dashboard: collect metrics (memory, keys, clients) and post to Telegram health topic.
# Use when Redis is configured (e.g. OpenClaw skill, gateway auth, or cache layer).
#
# Usage:
#   redis-dashboard.sh           — run and post to Telegram health topic
#   redis-dashboard.sh --dry-run — run without posting, print to stdout
#
# Env:  REDIS_URL (default: redis://localhost:6379), WORKSPACE_ROOT
#       TELEGRAM_* (from .env) for posting
# Cron: Add via cron/jobs.json or system crontab
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
REDIS_URL="${REDIS_URL:-redis://localhost:6379}"

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

# Parse Redis URL for redis-cli
# redis://host:port or redis://:password@host:port
parse_redis_url() {
  case "$REDIS_URL" in
    redis://*)
      REST="${REDIS_URL#redis://}"
      if [ -n "${REST#*@}" ] && [ "$REST" != "${REST#*@}" ]; then
        # password@host:port
        PASS="${REST%%@*}"
        HOST_PORT="${REST#*@}"
      else
        HOST_PORT="$REST"
        PASS=""
      fi
      HOST="${HOST_PORT%%:*}"
      PORT="${HOST_PORT#*:}"
      PORT="${PORT%%/*}"
      PORT="${PORT:-6379}"
      ;;
    *)
      HOST="localhost"
      PORT="6379"
      ;;
  esac
}

parse_redis_url

TMP_REPORT=$(mktemp)
trap 'rm -f "$TMP_REPORT"' EXIT INT TERM

collect_redis_info() {
  if ! command -v redis-cli >/dev/null 2>&1; then
    echo "redis-cli not found; skipping Redis dashboard"
    return 1
  fi

  # Try -u for URL-style, fallback to -h/-p
  if redis-cli -u "$REDIS_URL" ping 2>/dev/null | grep -q PONG; then
    INFO=$(redis-cli -u "$REDIS_URL" INFO server 2>/dev/null) || true
    INFO_MEM=$(redis-cli -u "$REDIS_URL" INFO memory 2>/dev/null) || true
    INFO_STATS=$(redis-cli -u "$REDIS_URL" INFO stats 2>/dev/null) || true
    INFO_CLIENTS=$(redis-cli -u "$REDIS_URL" INFO clients 2>/dev/null) || true
    DBSIZE=$(redis-cli -u "$REDIS_URL" DBSIZE 2>/dev/null) || echo "0"
  elif redis-cli -h "$HOST" -p "$PORT" ping 2>/dev/null | grep -q PONG; then
    INFO=$(redis-cli -h "$HOST" -p "$PORT" INFO server 2>/dev/null) || true
    INFO_MEM=$(redis-cli -h "$HOST" -p "$PORT" INFO memory 2>/dev/null) || true
    INFO_STATS=$(redis-cli -h "$HOST" -p "$PORT" INFO stats 2>/dev/null) || true
    INFO_CLIENTS=$(redis-cli -h "$HOST" -p "$PORT" INFO clients 2>/dev/null) || true
    DBSIZE=$(redis-cli -h "$HOST" -p "$PORT" DBSIZE 2>/dev/null) || echo "0"
  else
    echo "Redis unreachable at $REDIS_URL"
    return 1
  fi

  # Extract metrics
  USED_MEMORY=$(echo "$INFO_MEM" | grep '^used_memory_human:' | cut -d: -f2 | tr -d '\r')
  USED_MEMORY="${USED_MEMORY:-?}"
  CONNECTED_CLIENTS=$(echo "$INFO_CLIENTS" | grep '^connected_clients:' | cut -d: -f2 | tr -d '\r')
  CONNECTED_CLIENTS="${CONNECTED_CLIENTS:-?}"
  TOTAL_KEYS=$(echo "$DBSIZE" | grep -oE '[0-9]+' || echo "?")
  UPTIME_SEC=$(echo "$INFO" | grep '^uptime_in_seconds:' | cut -d: -f2 | tr -d '\r')
  UPTIME_DAYS="?"
  if [ -n "$UPTIME_SEC" ] && [ "$UPTIME_SEC" != "?" ]; then
    UPTIME_DAYS=$((UPTIME_SEC / 86400))
  fi

  # Build report (Telegram Markdown)
  {
    echo "🔴 *Redis Dashboard* — $(date +%Y-%m-%d)"
    echo ""
    echo "📦 *Memory:* ${USED_MEMORY}"
    echo "🔑 *Keys:* ${TOTAL_KEYS}"
    echo "👥 *Clients:* ${CONNECTED_CLIENTS}"
    echo "⏱ *Uptime:* ${UPTIME_DAYS} days"
    echo ""
    echo "_${REDIS_URL}_"
  } >"$TMP_REPORT"

  return 0
}

main() {
  if ! collect_redis_info; then
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "Redis dashboard skipped (redis-cli unavailable or Redis unreachable)"
    fi
    exit 0
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    echo "--- Dry run: would post to health topic ---"
    cat "$TMP_REPORT"
    echo "---"
    return 0
  fi

  if "$WORKSPACE_ROOT/tools/telegram-post.sh" health <"$TMP_REPORT"; then
    : # success
  else
    echo "redis-dashboard.sh: failed to post to Telegram" >&2
    exit 1
  fi
}

main

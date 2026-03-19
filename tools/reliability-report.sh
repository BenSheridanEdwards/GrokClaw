#!/bin/sh
# Nightly reliability report: gateway uptime, failed retries, merged PRs.
# Posts to Telegram health-alerts topic (4) at 07:00 WIB.
#
# Usage:
#   reliability-report.sh           — run and post to Telegram
#   reliability-report.sh --dry-run — run without posting, print to stdout
#
# Cron: 0 7 * * * (7am daily)
# Env:  WORKSPACE_ROOT, TELEGRAM_* (from .env)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
LOG_DIR="$WORKSPACE_ROOT/logs"
LOG_FILE="$LOG_DIR/reliability-$(date +%Y%m%d).log"
REPO="${GITHUB_REPO:-BenSheridanEdwards/GrokClaw}"
GATEWAY_PORT="${OPENCLAW_GATEWAY_PORT:-18800}"
OPENCLAW_LOGS="${OPENCLAW_LOGS:-$HOME/.openclaw/logs}"

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

mkdir -p "$LOG_DIR"

# Use a unique temp file; clean up on any exit
TMP_REPORT=$(mktemp)
trap 'rm -f "$TMP_REPORT"' EXIT INT TERM

log() {
  echo "$(date '+%Y-%m-%dT%H:%M:%S%z') $*" >>"$LOG_FILE"
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "$*"
  fi
}

# --- Gateway status ---
get_gateway_status() {
  if command -v curl >/dev/null 2>&1; then
    if curl -sf --connect-timeout 3 "http://127.0.0.1:${GATEWAY_PORT}/health" >/dev/null 2>&1; then
      # Try to get uptime from launchctl (macOS) or process
      if [ -n "${HOME:-}" ] && [ -x "$(command -v launchctl 2>/dev/null)" ]; then
        OUT=$(launchctl print "gui/$(id -u)/com.grokclaw.gateway" 2>/dev/null) || true
        if echo "$OUT" | grep -q 'state = running'; then
          echo "up"
          return
        fi
      fi
      # Fallback: check if any openclaw process is running
      if command -v pgrep >/dev/null 2>&1; then
        if pgrep -f openclaw >/dev/null 2>&1; then
          echo "up"
          return
        fi
      fi
      echo "up"
      return
    fi
  fi
  echo "down"
}

# --- Failed retries / error count from last 10k lines of each log ---
get_failed_retries() {
  COUNT=0
  if [ -d "${OPENCLAW_LOGS}" ]; then
    for f in "${OPENCLAW_LOGS}"/*.log; do
      [ -f "$f" ] || continue
      N=$(tail -n 10000 "$f" 2>/dev/null | grep -ciE 'retry|fail|error' || true)
      N="${N:-0}"
      COUNT=$((COUNT + N))
    done
  fi
  echo "$COUNT"
}

# --- Merged PRs in last 24h ---
get_merged_prs() {
  # 24h ago in ISO format for comparison
  CUTOFF=$(date -d '24 hours ago' +%s 2>/dev/null) || \
  CUTOFF=$(date -v-24H +%s 2>/dev/null) || \
  CUTOFF=$(( $(date +%s) - 86400 ))

  if ! command -v gh >/dev/null 2>&1; then
    return
  fi

  gh pr list --repo "$REPO" --state merged --limit 50 \
    --json number,title,url,mergedAt 2>/dev/null | \
  python3 -c '
import json, sys
from datetime import datetime
try:
    cutoff = int("'"$CUTOFF"'")
    prs = json.load(sys.stdin)
    for p in prs:
        ma = p.get("mergedAt") or ""
        if not ma:
            continue
        try:
            mt = datetime.fromisoformat(ma.replace("Z", "+00:00")).timestamp()
        except Exception:
            mt = 0
        if mt >= cutoff:
            print("#%d: %s — %s" % (p["number"], p["title"], p["url"]))
except Exception:
    pass
' 2>/dev/null || true
}

# --- Build and post report ---
main() {
  GATEWAY=$(get_gateway_status)
  RETRIES=$(get_failed_retries)
  PRS=$(get_merged_prs)

  # Build report with newlines (Telegram Markdown)
  {
    echo "📊 *Nightly Reliability Report* — $(date +%Y-%m-%d)"
    echo ""
    echo "🔌 *Gateway:* ${GATEWAY}"
    echo "⚠️ *Log errors/retries (recent):* ${RETRIES}"
    echo ""

    if [ -n "$PRS" ]; then
      echo "🔀 *Merged PRs (24h):*"
      echo "$PRS"
    else
      echo "🔀 *Merged PRs (24h):* None"
    fi
  } >"$TMP_REPORT"

  # Graceful no-data: if all healthy, say so
  if [ "$GATEWAY" = "up" ] && [ "$RETRIES" = "0" ] && [ -z "$PRS" ]; then
    {
      echo "📊 *Nightly Reliability Report* — $(date +%Y-%m-%d)"
      echo ""
      echo "✅ All healthy. No merged PRs in last 24h."
    } >"$TMP_REPORT"
  fi

  log "Report generated. Gateway=$GATEWAY Retries=$RETRIES"

  if [ "$DRY_RUN" -eq 1 ]; then
    echo ""
    echo "--- Dry run: would post to health topic ---"
    cat "$TMP_REPORT"
    echo "---"
    return 0
  fi

  # Post to Telegram health topic (4)
  if "$WORKSPACE_ROOT/tools/telegram-post.sh" health <"$TMP_REPORT"; then
    log "Posted to Telegram health topic"
  else
    log "ERROR: Failed to post to Telegram"
    exit 1
  fi
}

main

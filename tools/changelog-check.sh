#!/bin/sh
# PicoClaw changelog check: compare installed version to last-checked state.
# Outputs structured summary only when a new version is detected.
# Run via PicoClaw cron (changelog-weekly-check) every Monday at 07:00.
#
# Usage: changelog-check.sh
# Env:   PICOCLAW_WORKSPACE — workspace root (default: derived from script path)
# Exit:  0 always; outputs NEW_VERSION_JSON when upgrade detected
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${PICOCLAW_WORKSPACE:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STATE_FILE="$WORKSPACE_ROOT/data/changelog-state.json"

# Get installed version from picoclaw (extract semver-like string)
get_installed_version() {
  if ! command -v picoclaw >/dev/null 2>&1; then
    echo ""
    return
  fi
  out=$(picoclaw version 2>/dev/null || true)
  # Extract version: digits.digits.digits or vX.Y.Z
  echo "$out" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?' | head -1 || echo "$out" | tr -d '\n' | head -c 64
}

# Read state file; output empty lastVersion if missing/invalid
read_state() {
  if [ ! -f "$STATE_FILE" ]; then
    echo '{"lastVersion":"","lastCheckedAt":""}'
    return
  fi
  if ! jq -e . "$STATE_FILE" >/dev/null 2>&1; then
    echo '{"lastVersion":"","lastCheckedAt":""}'
    return
  fi
  cat "$STATE_FILE"
}

# Write state file
write_state() {
  mkdir -p "$(dirname "$STATE_FILE")"
  printf '%s\n' "$1" >"$STATE_FILE"
}

# ISO timestamp
now_iso() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

CURRENT=$(get_installed_version)
NOW=$(now_iso)

# Normalize empty or whitespace-only to empty
CURRENT=$(echo "$CURRENT" | tr -d '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

STATE=$(read_state)
LAST_VERSION=$(echo "$STATE" | jq -r '.lastVersion // ""')
LAST_CHECKED=$(echo "$STATE" | jq -r '.lastCheckedAt // ""')

# Update state after each successful check
NEW_STATE=$(jq -n \
  --arg v "${CURRENT:-unknown}" \
  --arg t "$NOW" \
  '{lastVersion: $v, lastCheckedAt: $t}')
write_state "$NEW_STATE"

# First run or no previous version: record only, no "new version" report
if [ -z "$LAST_VERSION" ] || [ "$LAST_VERSION" = "unknown" ]; then
  exit 0
fi

# Same version: exit silently
if [ "$CURRENT" = "$LAST_VERSION" ]; then
  exit 0
fi

# No valid current version (picoclaw not installed): do not report upgrade
if [ -z "$CURRENT" ] || [ "$CURRENT" = "unknown" ]; then
  exit 0
fi

# New version detected: output structured JSON for agent to post to Slack
# Format: NEW_VERSION_JSON:<json> so agent can parse and post
SUMMARY=$(jq -n \
  --arg current "$CURRENT" \
  --arg previous "$LAST_VERSION" \
  --arg checked "$NOW" \
  '{
    new_version: $current,
    previous_version: $previous,
    checked_at: $checked,
    summary: ("PicoClaw upgrade available: " + $previous + " → " + $current + ". Consider upgrading manually."),
    slack_message: ("📦 PicoClaw update: " + $previous + " → " + $current + "\nConsider upgrading: picoclaw is at " + $current + ".")
  }')
echo "NEW_VERSION_JSON:$SUMMARY"

#!/bin/sh
# Check PicoClaw and OpenClaw GitHub releases for new versions. Posts to Slack when detected.
# Run via PicoClaw cron (cron/jobs.json) or system crontab.
#
# Usage: changelog-check.sh
# Env:   PICOCLAW_WORKSPACE — workspace root (default: derived from script path)
#        SLACK_CHANNEL_ID   — Slack channel for alerts (default: C0ALE1S0LSF)
# Exit:  0 on success, 1 on fetch/parse error
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${PICOCLAW_WORKSPACE:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STATE_FILE="$WORKSPACE_ROOT/.changelog-check-state"
SLACK_CHANNEL="${SLACK_CHANNEL_ID:-C0ALE1S0LSF}"

# Load .env for SLACK_BOT_TOKEN
if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

fetch_release() {
  repo="$1"
  python3 - "$repo" <<'PY'
import json
import sys
import urllib.request

repo = sys.argv[1]
url = f"https://api.github.com/repos/{repo}/releases/latest"
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        d = json.load(r)
except Exception:
    sys.exit(1)
tag = d.get("tag_name") or ""
name = d.get("name") or tag
html_url = d.get("html_url") or ""
body = (d.get("body") or "")[:400]
body = "".join(c if ord(c) >= 32 or c in "\n\t" else " " for c in body).replace("\n", " ")
if not tag:
    sys.exit(1)
print(f"{tag}|{name}|{html_url}|{body}")
PY
}

read_state() {
  if [ -f "$STATE_FILE" ]; then
    prev_picoclaw=$(grep "^picoclaw_tag=" "$STATE_FILE" 2>/dev/null | cut -d= -f2-)
    prev_openclaw=$(grep "^openclaw_tag=" "$STATE_FILE" 2>/dev/null | cut -d= -f2-)
    echo "${prev_picoclaw:-}|${prev_openclaw:-}"
  else
    echo "|"
  fi
}

write_state() {
  printf 'picoclaw_tag=%s\nopenclaw_tag=%s\n' "$1" "$2" >"$STATE_FILE"
}

post_slack() {
  "$WORKSPACE_ROOT/tools/slack-post.sh" "$SLACK_CHANNEL" "$1"
}

# Fetch current releases
picoclaw_data=$(fetch_release "sipeed/picoclaw") || { echo "Failed to fetch PicoClaw release" >&2; exit 1; }
openclaw_data=$(fetch_release "openclaw/openclaw") || { echo "Failed to fetch OpenClaw release" >&2; exit 1; }

picoclaw_tag=$(echo "$picoclaw_data" | cut -d'|' -f1)
openclaw_tag=$(echo "$openclaw_data" | cut -d'|' -f1)
picoclaw_name=$(echo "$picoclaw_data" | cut -d'|' -f2)
openclaw_name=$(echo "$openclaw_data" | cut -d'|' -f2)
picoclaw_url=$(echo "$picoclaw_data" | cut -d'|' -f3)
openclaw_url=$(echo "$openclaw_data" | cut -d'|' -f3)
picoclaw_body=$(echo "$picoclaw_data" | cut -d'|' -f4-)
openclaw_body=$(echo "$openclaw_data" | cut -d'|' -f4-)

prev=$(read_state)
prev_picoclaw=$(echo "$prev" | cut -d'|' -f1)
prev_openclaw=$(echo "$prev" | cut -d'|' -f2)
new_picoclaw=""
new_openclaw=""

# First run: record state, no alert
if [ -z "$prev_picoclaw" ] && [ -z "$prev_openclaw" ]; then
  write_state "$picoclaw_tag" "$openclaw_tag"
  exit 0
fi

[ -n "$prev_picoclaw" ] && [ "$picoclaw_tag" != "$prev_picoclaw" ] && new_picoclaw=1
[ -n "$prev_openclaw" ] && [ "$openclaw_tag" != "$prev_openclaw" ] && new_openclaw=1

if [ -z "$new_picoclaw" ] && [ -z "$new_openclaw" ]; then
  write_state "$picoclaw_tag" "$openclaw_tag"
  exit 0
fi

# Build Slack message
msg=""
if [ -n "$new_picoclaw" ]; then
  msg="📦 *New PicoClaw release:* ${picoclaw_name} (${picoclaw_tag})
${picoclaw_url}
${picoclaw_body}
"
fi
if [ -n "$new_openclaw" ]; then
  msg="${msg}📦 *New OpenClaw release:* ${openclaw_name} (${openclaw_tag})
${openclaw_url}
${openclaw_body}
"
fi

post_slack "$msg"
write_state "$picoclaw_tag" "$openclaw_tag"
exit 0

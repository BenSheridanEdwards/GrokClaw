#!/bin/sh
# Check for new OpenClaw releases and post to health-alerts if an update is available.
# Uses GitHub releases API to compare against the installed version.
#
# Usage: changelog-check.sh [--dry-run]
# Exit:  0 = up to date or update found, 1 = error
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in --dry-run) DRY_RUN=1 ;; esac
done

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

current_version=$(openclaw --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
if [ -z "$current_version" ]; then
  echo "changelog-check: could not determine installed version" >&2
  exit 1
fi

latest_json=$(curl -sf --connect-timeout 10 \
  "https://api.github.com/repos/nicepkg/openclaw/releases/latest" 2>/dev/null || echo "")

if [ -z "$latest_json" ]; then
  npm_version=$(curl -sf --connect-timeout 10 \
    "https://registry.npmjs.org/openclaw/latest" 2>/dev/null | \
    python3 -c "import json,sys; print(json.load(sys.stdin).get('version',''))" 2>/dev/null || echo "")

  if [ -z "$npm_version" ]; then
    echo "changelog-check: could not fetch latest version from GitHub or npm" >&2
    exit 1
  fi
  latest_version="$npm_version"
  release_url="https://www.npmjs.com/package/openclaw"
  release_notes=""
else
  latest_version=$(echo "$latest_json" | python3 -c "
import json, sys, re
d = json.load(sys.stdin)
tag = d.get('tag_name', '')
m = re.search(r'[0-9]+\.[0-9]+\.[0-9]+', tag)
print(m.group(0) if m else '')
" 2>/dev/null)
  release_url=$(echo "$latest_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('html_url',''))" 2>/dev/null)
  release_notes=$(echo "$latest_json" | python3 -c "
import json, sys
body = json.load(sys.stdin).get('body', '')
print(body[:300] if body else '')
" 2>/dev/null)
fi

if [ -z "$latest_version" ]; then
  echo "changelog-check: could not parse latest version" >&2
  exit 1
fi

echo "Installed: v${current_version}"
echo "Latest:    v${latest_version}"

if [ "$current_version" = "$latest_version" ]; then
  echo "Up to date."
  if [ "$DRY_RUN" -eq 0 ]; then
    "$WORKSPACE_ROOT/tools/cron-run-record.sh" changelog-weekly-check grok ok "up to date at v${current_version}" 2>/dev/null || true
  fi
  exit 0
fi

update_msg="OpenClaw update available: v${current_version} -> v${latest_version}"
if [ -n "$release_url" ]; then
  update_msg="$update_msg ($release_url)"
fi
if [ -n "$release_notes" ]; then
  update_msg="$update_msg. Notes: ${release_notes}"
fi

echo "$update_msg"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "(dry-run: would post to Telegram)"
  exit 0
fi

"$WORKSPACE_ROOT/tools/telegram-post.sh" health "$update_msg" 2>/dev/null || true
"$WORKSPACE_ROOT/tools/cron-run-record.sh" changelog-weekly-check grok ok "update available: v${current_version} -> v${latest_version}" 2>/dev/null || true
exit 0

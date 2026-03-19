#!/bin/sh
# Pull latest main and restart OpenClaw gateway via launchd.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STATE_FILE="$WORKSPACE_ROOT/.last-deploy-sha"

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

cd "$WORKSPACE_ROOT"

current_sha="$(git rev-parse HEAD)"
git fetch origin main --quiet
remote_sha="$(git rev-parse origin/main)"

if [ "$current_sha" = "$remote_sha" ]; then
  echo "No deploy needed (already at origin/main)."
  exit 0
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  "$WORKSPACE_ROOT/tools/telegram-post.sh" health \
    "Deploy blocked: working tree is dirty. Commit or stash local changes before auto-deploy."
  echo "Deploy blocked due to dirty working tree." >&2
  exit 2
fi

commit_line="$(git log -1 --pretty=format:'%h %s' origin/main)"
"$WORKSPACE_ROOT/tools/telegram-post.sh" health "Deploying ${commit_line}"

git pull --ff-only origin main
new_sha="$(git rev-parse HEAD)"
printf '%s\n' "$new_sha" > "$STATE_FILE"

"$WORKSPACE_ROOT/tools/gateway-ctl.sh" restart
sleep 10

if "$WORKSPACE_ROOT/tools/health-check.sh" >/dev/null 2>&1; then
  "$WORKSPACE_ROOT/tools/telegram-post.sh" health "Deploy complete. Gateway healthy at $(git rev-parse --short HEAD)."
  echo "Deploy successful: $new_sha"
  exit 0
fi

"$WORKSPACE_ROOT/tools/telegram-post.sh" health "Deploy failed health check after restart. Manual intervention required."
echo "Deploy failed health check" >&2
exit 1

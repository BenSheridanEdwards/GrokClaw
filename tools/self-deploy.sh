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

if ! python3 "$WORKSPACE_ROOT/tools/cron-jobs-tool.py" validate; then
  echo "Deploy blocked: cron/jobs.json failed validation (Telegram delivery config)." >&2
  exit 3
fi

current_sha="$(git rev-parse HEAD)"
git fetch origin main --quiet
remote_sha="$(git rev-parse origin/main)"

if [ "$current_sha" = "$remote_sha" ]; then
  echo "No deploy needed (already at origin/main)."
  exit 0
fi

# Auto-commit local operational changes (memory, docs updated by agents)
# so they don't block deploy. Uses union merge driver via .gitattributes.
if ! git diff --quiet -- memory/ || ! git diff --quiet -- docs/; then
  git add memory/ docs/
  git commit -m "chore: auto-commit agent memory/docs updates before deploy" --no-verify || true
fi

# Stash any remaining dirty files (tools being edited, etc.)
stashed=0
if ! git diff --quiet || ! git diff --cached --quiet; then
  git stash push -m "self-deploy auto-stash $(date +%Y%m%d-%H%M%S)" --quiet
  stashed=1
fi

commit_line="$(git log -1 --pretty=format:'%h %s' origin/main)"
"$WORKSPACE_ROOT/tools/telegram-post.sh" health "Deploying ${commit_line}"

# Rebase local commits (memory updates) on top of remote.
# .gitattributes merge=union on MEMORY.md prevents conflicts.
if ! git pull --rebase origin main; then
  echo "Rebase failed; attempting auto-resolve..." >&2
  if git diff --name-only --diff-filter=U | grep -q '^memory/'; then
    git checkout --theirs memory/MEMORY.md 2>/dev/null || true
    git add memory/MEMORY.md
    GIT_EDITOR=true git rebase --continue 2>/dev/null || true
  fi
  if ! git rebase --skip 2>/dev/null; then
    git rebase --abort 2>/dev/null || true
    git pull --ff-only origin main 2>/dev/null || true
  fi
fi

if [ "$stashed" -eq 1 ]; then
  git stash pop --quiet 2>/dev/null || true
fi
new_sha="$(git rev-parse HEAD)"
printf '%s\n' "$new_sha" > "$STATE_FILE"

"$WORKSPACE_ROOT/tools/sync-cron-jobs.sh" --restart
sleep 10

if "$WORKSPACE_ROOT/tools/health-check.sh" >/dev/null 2>&1; then
  "$WORKSPACE_ROOT/tools/telegram-post.sh" health "Deploy complete. Gateway healthy at $(git rev-parse --short HEAD)."
  echo "Deploy successful: $new_sha"
  exit 0
fi

"$WORKSPACE_ROOT/tools/telegram-post.sh" health "Deploy failed health check after restart. Manual intervention required."
echo "Deploy failed health check" >&2
exit 1

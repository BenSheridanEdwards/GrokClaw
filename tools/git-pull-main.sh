#!/bin/sh
# Pull origin/main with rebase and tags even when the tree has local edits.
# Same stash pattern as self-deploy.sh — avoids "cannot pull with rebase" on dirty trees.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
cd "$WORKSPACE_ROOT"

stashed=0
if ! git diff --quiet || ! git diff --cached --quiet; then
  git stash push -m "git-pull-main auto-stash $(date +%Y%m%d-%H%M%S)"
  stashed=1
fi

cleanup_stash() {
  if [ "$stashed" -eq 1 ]; then
    git stash pop || {
      echo "Pull finished but stash pop failed; resolve conflicts, then git stash drop if appropriate." >&2
      exit 1
    }
  fi
}

if ! git pull --rebase --tags origin main; then
  if [ "$stashed" -eq 1 ]; then
    git stash pop --quiet 2>/dev/null || true
  fi
  exit 1
fi

cleanup_stash

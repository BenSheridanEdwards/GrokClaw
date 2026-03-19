#!/bin/sh
# Create a feature branch and draft PR for an approved Grok suggestion.
# Usage: create-pr.sh <linear-issue-id> <title>
#
# The PR body instructs Cursor exactly what to implement.
# Env:   WORKSPACE_ROOT — workspace root (default: derived from script path)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <linear-issue-id> <title>" >&2
  exit 1
fi

LINEAR_ISSUE_ID="$1"
shift
SUGGESTION_TITLE="$*"

REPO="${GITHUB_REPO:-BenSheridanEdwards/GrokClaw}"
BRANCH="grok/${LINEAR_ISSUE_ID}"
LINEAR_URL="https://linear.app/grokclaw/issue/${LINEAR_ISSUE_ID}"

cd "$WORKSPACE_ROOT"

git fetch origin main --quiet
git checkout -B "$BRANCH" origin/main --quiet

git commit --allow-empty -m "chore: scaffold ${LINEAR_ISSUE_ID} — ${SUGGESTION_TITLE}

Linear: ${LINEAR_URL}
"

git push origin "$BRANCH" --quiet

PR_URL=$(gh pr create \
  --repo "$REPO" \
  --base main \
  --head "$BRANCH" \
  --title "Implement ${LINEAR_ISSUE_ID} — ${SUGGESTION_TITLE}" \
  --body "## What to implement

**${SUGGESTION_TITLE}**

Linear ticket: ${LINEAR_URL}

Read the Linear ticket description for the full spec before starting.

## Instructions for Cursor

1. Read \`CURSOR.md\` in the repo root — it contains your full operating instructions.
2. Read the Linear ticket at ${LINEAR_URL} for the implementation spec.
3. Implement the feature with real code/config/scripts in this branch.
4. Commit with a message referencing \`${LINEAR_ISSUE_ID}\`.
5. When done, run \`gh pr ready <pr-number> --repo ${REPO}\` to mark ready for review.
6. Post to Telegram: \`tools/telegram-post.sh suggestions \"🤖 ${LINEAR_ISSUE_ID} complete. PR: <url>\"\`

## Acceptance criteria

- [ ] Feature described in the Linear ticket is implemented and working
- [ ] Real file changes present in this PR (not just the scaffold commit)
- [ ] Scripts are executable and tested
- [ ] PR marked ready for review
- [ ] Completion posted to Telegram" \
  --draft 2>&1)

echo "$PR_URL"

git checkout main --quiet

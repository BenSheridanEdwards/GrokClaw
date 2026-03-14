#!/bin/sh
set -eu

if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
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

# Ensure we're working in the workspace repo
cd /Users/jarvis/.picoclaw/workspace

# Fetch latest main and create branch
git fetch origin main --quiet
git checkout -B "$BRANCH" origin/main --quiet

# Create an empty commit so the branch has something to push
git commit --allow-empty -m "chore: scaffold ${LINEAR_ISSUE_ID} — ${SUGGESTION_TITLE}

Linear: https://linear.app/grokclaw/issue/${LINEAR_ISSUE_ID}
"

git push origin "$BRANCH" --quiet

# Open a draft PR linked back to the Linear issue
PR_URL=$(gh pr create \
  --repo "$REPO" \
  --base main \
  --head "$BRANCH" \
  --title "Implement ${LINEAR_ISSUE_ID} — ${SUGGESTION_TITLE}" \
  --body "$(cat <<EOF
## Summary

Implements Grok suggestion tracked in Linear: https://linear.app/grokclaw/issue/${LINEAR_ISSUE_ID}

## Linear

Closes ${LINEAR_ISSUE_ID}

## Notes

This PR was auto-scaffolded by Grok on approval. Cursor is assigned and will implement the work.
EOF
)" \
  --draft 2>&1)

echo "$PR_URL"

# Return to main
git checkout main --quiet

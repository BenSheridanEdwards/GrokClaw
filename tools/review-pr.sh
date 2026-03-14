#!/bin/sh
# Fetch a PR diff and changed file list, print to stdout for Grok to review.
# Usage: review-pr.sh <pr-number>
set -eu

REPO="${GITHUB_REPO:-BenSheridanEdwards/GrokClaw}"
PR="$1"

echo "=== PR #${PR} DETAILS ==="
gh pr view "$PR" --repo "$REPO" --json number,title,state,isDraft,headRefName,body \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'Title:  {d[\"title\"]}')
print(f'Branch: {d[\"headRefName\"]}')
print(f'Draft:  {d[\"isDraft\"]}')
print(f'State:  {d[\"state\"]}')
"

echo ""
echo "=== CHANGED FILES ==="
gh pr view "$PR" --repo "$REPO" --json files \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
for f in d.get('files', []):
    additions = f.get('additions', 0)
    deletions = f.get('deletions', 0)
    print(f'  {f[\"path\"]}  (+{additions} -{deletions})')
"

echo ""
echo "=== DIFF (first 200 lines) ==="
gh pr diff "$PR" --repo "$REPO" 2>/dev/null | head -200

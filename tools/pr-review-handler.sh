#!/bin/sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

REPO="${GROKCLAW_GITHUB_REPO:-${GITHUB_REPO:-BenSheridanEdwards/GrokClaw}}"
TELEGRAM_INLINE="$WORKSPACE_ROOT/tools/telegram-inline.sh"
LINEAR_TRANSITION="$WORKSPACE_ROOT/tools/linear-transition.sh"
LINEAR_BASE_URL="${LINEAR_BASE_URL:-https://linear.app/grokclaw/issue}"

usage() {
  cat <<'EOF' >&2
usage:
  pr-review-handler.sh list
  pr-review-handler.sh approve <pr-number> <linear-issue-id> "<telegram-summary>" "<review-body>"
  pr-review-handler.sh request-changes <pr-number> "<review-body>"
EOF
  exit 1
}

render_queue() {
  python3 -c '
import json
import sys

items = json.load(sys.stdin)
if not items:
    print("No PRs waiting for Grok review.")
    raise SystemExit(0)

for item in items:
    draft = " draft" if item.get("isDraft") else ""
    ref = item.get("headRefName") or "unknown-branch"
    print("#{} {} [{}{}] {}".format(
        item["number"],
        item.get("title", "").strip(),
        ref,
        draft,
        item.get("url", ""),
    ))
'
}

pr_metadata() {
  gh pr view "$1" --repo "$REPO" --json number,title,url,headRefName
}

queue_list() {
  gh pr list --repo "$REPO" --state open --label needs-grok-review --json number,title,url,headRefName,isDraft | render_queue
}

set_review_labels() {
  pr_number="$1"
  shift
  gh pr edit "$pr_number" --repo "$REPO" "$@"
}

approve_pr() {
  [ "$#" -eq 4 ] || usage
  pr_number="$1"
  linear_issue="$2"
  telegram_summary="$3"
  review_body="$4"

  gh pr review "$pr_number" --repo "$REPO" --approve --body "$review_body"
  set_review_labels "$pr_number" --remove-label needs-grok-review --add-label grok-approved
  "$LINEAR_TRANSITION" "$linear_issue" "In Review"

  pr_json="$(pr_metadata "$pr_number")"
  pr_title="$(printf '%s' "$pr_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["title"])')"
  pr_url="$(printf '%s' "$pr_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["url"])')"
  buttons="$(python3 - "$pr_number" "$linear_issue" <<'PY'
import json
import sys

pr_number = sys.argv[1]
issue_id = sys.argv[2]
print(json.dumps([
    {"text": "Merge", "callback_data": f"merge:{pr_number}:{issue_id}"},
    {"text": "Reject", "callback_data": f"reject:{pr_number}:{issue_id}"},
], separators=(",", ":")))
PY
)"
  message="$(cat <<EOF
Grok approved PR #$pr_number: $pr_title
$telegram_summary
PR: $pr_url
Linear: $LINEAR_BASE_URL/$linear_issue
EOF
)"

  "$TELEGRAM_INLINE" pr-reviews "$message" "$buttons" plain
}

request_changes() {
  [ "$#" -eq 2 ] || usage
  pr_number="$1"
  review_body="$2"

  gh pr review "$pr_number" --repo "$REPO" --request-changes --body "$review_body"
  set_review_labels "$pr_number" --remove-label grok-approved --remove-label needs-grok-review
}

command="${1:-}"
[ -n "$command" ] || usage
shift || true

case "$command" in
  list) queue_list "$@" ;;
  approve) approve_pr "$@" ;;
  request-changes) request_changes "$@" ;;
  *) usage ;;
esac

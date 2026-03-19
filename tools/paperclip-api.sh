#!/usr/bin/env bash
set -euo pipefail

# Paperclip API helper — wraps common Paperclip API calls for agent use.
# Usage:
#   paperclip-api.sh get-issue <issue-id>
#   paperclip-api.sh update-issue <issue-id> <status> [comment]
#   paperclip-api.sh comment <issue-id> <body>
#   paperclip-api.sh list-issues [status]
#   paperclip-api.sh create-issue <title> <description> [priority]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KEY_FILE="${HOME}/.openclaw/workspace/paperclip-claimed-api-key.json"
API_BASE="http://127.0.0.1:3100/api"
COMPANY_ID="2e003f55-4bdf-465b-acd3-143ce3745aa8"
AGENT_ID="b5bb9ffe-2b4e-437a-b7d7-feee36da31fb"

if [ -f "$KEY_FILE" ]; then
  TOKEN=$(python3 -c "import json; print(json.load(open('$KEY_FILE'))['token'])" 2>/dev/null || echo "")
else
  TOKEN=""
fi

auth_header() {
  if [ -n "$TOKEN" ]; then
    echo "Authorization: Bearer $TOKEN"
  else
    echo "X-Paperclip-Local: true"
  fi
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  get-issue)
    issue_id="${1:?Usage: paperclip-api.sh get-issue <issue-id>}"
    curl -sf "${API_BASE}/issues/${issue_id}" \
      -H "$(auth_header)" \
      -H "Content-Type: application/json" | python3 -m json.tool
    ;;

  update-issue)
    issue_id="${1:?Usage: paperclip-api.sh update-issue <issue-id> <status> [comment]}"
    status="${2:?Missing status (todo|in_progress|in_review|done|cancelled)}"
    comment="${3:-}"
    payload="{\"status\":\"${status}\"}"
    if [ -n "$comment" ]; then
      payload=$(python3 -c "import json; print(json.dumps({'status':'${status}','comment':'${comment}'}))")
    fi
    curl -sf -X PATCH "${API_BASE}/issues/${issue_id}" \
      -H "$(auth_header)" \
      -H "Content-Type: application/json" \
      -d "$payload" | python3 -m json.tool
    ;;

  comment)
    issue_id="${1:?Usage: paperclip-api.sh comment <issue-id> <body>}"
    body="${2:?Missing comment body}"
    payload=$(python3 -c "import json; print(json.dumps({'body': '$body'}))")
    curl -sf -X POST "${API_BASE}/issues/${issue_id}/comments" \
      -H "$(auth_header)" \
      -H "Content-Type: application/json" \
      -d "$payload" | python3 -m json.tool
    ;;

  list-issues)
    status_filter="${1:-}"
    url="${API_BASE}/companies/${COMPANY_ID}/issues"
    if [ -n "$status_filter" ]; then
      url="${url}?status=${status_filter}&assigneeAgentId=${AGENT_ID}"
    fi
    curl -sf "$url" \
      -H "$(auth_header)" \
      -H "Content-Type: application/json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('items', [])
for i in items:
    print(f'[{i.get(\"identifier\",\"?\")}] {i[\"status\"]:12s} | {i[\"title\"][:70]}')
if not items:
    print('No issues found.')
"
    ;;

  create-issue)
    title="${1:?Usage: paperclip-api.sh create-issue <title> <description> [priority]}"
    description="${2:?Missing description}"
    priority="${3:-medium}"
    payload=$(python3 -c "
import json
print(json.dumps({
    'title': '''$title''',
    'description': '''$description''',
    'status': 'todo',
    'priority': '$priority',
    'assigneeAgentId': '$AGENT_ID'
}))
")
    curl -sf -X POST "${API_BASE}/companies/${COMPANY_ID}/issues" \
      -H "$(auth_header)" \
      -H "Content-Type: application/json" \
      -d "$payload" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'Created: {d.get(\"identifier\",\"?\")} — {d[\"title\"]}')
print(f'ID: {d[\"id\"]}')
"
    ;;

  health)
    curl -sf "${API_BASE}/health" | python3 -m json.tool
    ;;

  *)
    echo "Paperclip API helper"
    echo "Commands:"
    echo "  get-issue <id>                          Get issue details"
    echo "  update-issue <id> <status> [comment]    Update issue status"
    echo "  comment <id> <body>                     Add comment to issue"
    echo "  list-issues [status]                    List issues (optionally filtered)"
    echo "  create-issue <title> <desc> [priority]  Create new issue"
    echo "  health                                  Check API health"
    ;;
esac

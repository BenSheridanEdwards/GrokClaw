#!/bin/sh
set -eu

if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <suggestion-number> <title>" >&2
  exit 1
fi

SUGGESTION_NUMBER="$1"
shift
SUGGESTION_TITLE="$*"

LINEAR_API_KEY="${LINEAR_API_KEY:-}"
LINEAR_TEAM_ID="${LINEAR_TEAM_ID:-3f1b1054-07c6-4aad-a02c-89c78a43946b}"
LINEAR_ASSIGNEE_NAME="${LINEAR_ASSIGNEE_NAME:-}"

if [ -z "$LINEAR_API_KEY" ]; then
  echo "LINEAR_API_KEY is not configured" >&2
  exit 1
fi

if [ -z "$LINEAR_TEAM_ID" ]; then
  echo "LINEAR_TEAM_ID is not configured" >&2
  exit 1
fi

query() {
  curl -fsS https://api.linear.app/graphql \
    -H "Content-Type: application/json" \
    -H "Authorization: $LINEAR_API_KEY" \
    --data-binary "$1"
}

json_escape() {
  python3 - <<'PY' "$1"
import json, sys
print(json.dumps(sys.argv[1]))
PY
}

assignee_id=""
if [ -n "$LINEAR_ASSIGNEE_NAME" ]; then
  lookup_user_payload=$(cat <<EOF
{"query":"query LookupUser(\$name: String!) { users(filter: { name: { eq: \$name } }) { nodes { id name } } }","variables":{"name":$(
  json_escape "$LINEAR_ASSIGNEE_NAME"
)}} 
EOF
)

  user_response=$(query "$lookup_user_payload" || true)
  assignee_id=$(
    python3 - <<'PY' "$user_response"
import json, sys
raw = sys.argv[1]
if not raw:
    print("")
    raise SystemExit
data = json.loads(raw)
nodes = (((data.get("data") or {}).get("users") or {}).get("nodes") or [])
print(nodes[0]["id"] if nodes else "")
PY
  )
fi

title="Implement Grok Suggestion #$SUGGESTION_NUMBER - $SUGGESTION_TITLE"

if [ -n "$assignee_id" ]; then
  create_payload=$(cat <<EOF
{"query":"mutation CreateIssue(\$teamId: String!, \$title: String!, \$assigneeId: String!) { issueCreate(input: { teamId: \$teamId, title: \$title, assigneeId: \$assigneeId }) { success issue { id identifier title url } } }","variables":{"teamId":$(
  json_escape "$LINEAR_TEAM_ID"
),"title":$(
  json_escape "$title"
),"assigneeId":$(
  json_escape "$assignee_id"
)}} 
EOF
)
else
  create_payload=$(cat <<EOF
{"query":"mutation CreateIssue(\$teamId: String!, \$title: String!) { issueCreate(input: { teamId: \$teamId, title: \$title }) { success issue { id identifier title url } } }","variables":{"teamId":$(
  json_escape "$LINEAR_TEAM_ID"
),"title":$(
  json_escape "$title"
)}} 
EOF
)
fi

create_response=$(query "$create_payload")

python3 - <<'PY' "$create_response"
import json, sys
data = json.loads(sys.argv[1])
errors = data.get("errors") or []
if errors:
    raise SystemExit(errors[0].get("message", "Linear issueCreate failed"))
result = ((data.get("data") or {}).get("issueCreate") or {})
if not result.get("success"):
    raise SystemExit("Linear issueCreate returned success=false")
issue = result.get("issue") or {}
url = issue.get("url", "")
if not url:
    raise SystemExit("Linear issue URL missing from response")
print(url)
PY

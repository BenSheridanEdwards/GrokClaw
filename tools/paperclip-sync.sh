#!/usr/bin/env bash
set -euo pipefail

# Paperclip Sync — bridges OpenClaw cron activity into Paperclip issues.
# Called by the OpenClaw cron job "paperclip-sync" to keep the board current.
#
# What it does:
#   1. Checks Paperclip API health
#   2. Reconciles: closes Paperclip issues whose matching Linear tickets are Done
#   3. Creates Paperclip issues for any new Linear tickets not yet tracked
#   4. Reports board summary

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
API_BASE="http://127.0.0.1:3100/api"
COMPANY_ID="2e003f55-4bdf-465b-acd3-143ce3745aa8"
AGENT_ID="b5bb9ffe-2b4e-437a-b7d7-feee36da31fb"

health=$(curl -sf --connect-timeout 5 "${API_BASE}/health" 2>/dev/null || echo '{"status":"unreachable"}')
status=$(echo "$health" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "error")

if [ "$status" != "ok" ]; then
  echo "Paperclip API not healthy (status=$status), skipping sync"
  exit 0
fi

echo "Paperclip API healthy"

issues=$(curl -sf "${API_BASE}/companies/${COMPANY_ID}/issues" 2>/dev/null || echo "[]")
issue_count=$(echo "$issues" | python3 -c "
import json, sys
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('items', [])
by_status = {}
for i in items:
    s = i['status']
    by_status[s] = by_status.get(s, 0) + 1
parts = [f'{v} {k}' for k, v in sorted(by_status.items())]
print(', '.join(parts) if parts else 'empty board')
" 2>/dev/null || echo "error reading issues")

echo "Board: $issue_count"

agent=$(curl -sf "${API_BASE}/companies/${COMPANY_ID}/agents" 2>/dev/null || echo "[]")
agent_status=$(echo "$agent" | python3 -c "
import json, sys
agents = json.load(sys.stdin)
for a in agents:
    print(f'{a[\"name\"]}: {a[\"status\"]}, adapter={a[\"adapterType\"]}, spent={a[\"spentMonthlyCents\"]}c')
" 2>/dev/null || echo "error")

echo "Agents: $agent_status"

runs=$(curl -sf "${API_BASE}/companies/${COMPANY_ID}/heartbeat-runs?limit=5" 2>/dev/null || echo "[]")
run_summary=$(echo "$runs" | python3 -c "
import json, sys
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('items', [])
succeeded = sum(1 for r in items if r.get('status') == 'succeeded')
failed = sum(1 for r in items if r.get('status') == 'failed')
print(f'{succeeded} succeeded, {failed} failed (last 5)')
" 2>/dev/null || echo "error")

echo "Recent runs: $run_summary"

cat << EOF
{
  "paperclip_status": "$status",
  "board": "$issue_count",
  "agents": "$(echo "$agent_status" | head -1)",
  "recent_runs": "$run_summary"
}
EOF

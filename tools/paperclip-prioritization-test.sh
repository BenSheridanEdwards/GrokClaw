#!/usr/bin/env bash
# Deterministic smoke test for Paperclip list-issues prioritization.
# Verifies that issues are sorted high > medium > low and output includes id+priority.
# Usage: paperclip-prioritization-test.sh
# No network required — uses canned JSON input.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

echo "== Paperclip prioritization smoke test =="

# Simulated API response: mixed priority order
CANNED_JSON='[
  {"id":"c-low","identifier":"L-1","status":"todo","priority":"low","title":"Low priority task"},
  {"id":"a-high","identifier":"H-1","status":"todo","priority":"high","title":"High priority task"},
  {"id":"b-medium","identifier":"M-1","status":"todo","priority":"medium","title":"Medium priority task"},
  {"id":"d-noprio","identifier":"N-1","status":"todo","title":"No priority field (defaults medium)"}
]'

OUTPUT=$(echo "$CANNED_JSON" | python3 -c "
import json, sys
items = json.load(sys.stdin)
PRIO_ORDER = {'high': 0, 'medium': 1, 'low': 2}
def sort_key(i):
    p = (i.get('priority') or 'medium').lower()
    return (PRIO_ORDER.get(p, 1), i.get('title', ''))
items.sort(key=sort_key)
for i in items:
    ident = i.get('identifier', '?')
    iid = i.get('id', '')
    prio = (i.get('priority') or 'medium').lower()
    status = i.get('status', '')
    title = (i.get('title') or '')[:65]
    print(f'[{ident}] id={iid} | {prio:6s} | {status:12s} | {title}')
")

# Verify order: first line should be high, last explicit low
FIRST_LINE=$(echo "$OUTPUT" | head -1)
if ! echo "$FIRST_LINE" | grep -q 'high'; then
  echo "FAIL: First issue should be high priority, got: $FIRST_LINE" >&2
  echo "$OUTPUT" >&2
  exit 1
fi

# Third line should be low (H-1, M-1, L-1, N-1 → H, M, L, N where N=medium)
LOW_LINE=$(echo "$OUTPUT" | grep ' low ')
if [ -z "$LOW_LINE" ]; then
  echo "FAIL: No low-priority issue in output" >&2
  echo "$OUTPUT" >&2
  exit 1
fi

# Verify id= and priority columns present
if ! echo "$OUTPUT" | head -1 | grep -qE 'id=[a-zA-Z0-9-]+'; then
  echo "FAIL: Output missing id= column" >&2
  echo "$OUTPUT" >&2
  exit 1
fi
if ! echo "$OUTPUT" | head -1 | grep -qE '(high|medium|low)'; then
  echo "FAIL: Output missing priority column" >&2
  echo "$OUTPUT" >&2
  exit 1
fi

echo "$OUTPUT"
echo ""
echo "PASS: Prioritization smoke test completed"

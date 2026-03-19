#!/bin/sh
# Transition a Linear issue to a new workflow state.
# Usage: linear-transition.sh <issue-id> <state>
#
# States: Backlog, Todo, In Progress, In Review, Done, Canceled
# Example: linear-transition.sh GRO-17 Done
#
# Env: WORKSPACE_ROOT — workspace root (default: derived from script path)
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
  echo "usage: $0 <issue-id> <state>" >&2
  echo "  States: Backlog, Todo, In Progress, In Review, Done, Canceled" >&2
  exit 1
fi

ISSUE_ID="$1"
TARGET_STATE="$2"

"$WORKSPACE_ROOT/tools/retry.sh" --max 3 --delay 2 --alert health -- \
  python3 "$WORKSPACE_ROOT/tools/_linear_transition.py" \
    "$LINEAR_API_KEY" \
    "$ISSUE_ID" \
    "$TARGET_STATE"

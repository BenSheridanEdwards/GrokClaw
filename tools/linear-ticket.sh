#!/bin/sh
# Create a Linear ticket only from an approved Telegram draft.
# Usage: linear-ticket.sh <reference-id> <title> [description]
#
# Prints the Linear issue URL on success.
# Env:
#   WORKSPACE_ROOT
#   LINEAR_CREATION_FLOW   suggestion | user_request
#   LINEAR_DRAFT_ID        pending draft id previously approved in Telegram
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
  echo "usage: $0 <reference-id> <title> [description]" >&2
  exit 1
fi

REFERENCE_ID="$1"; shift
TITLE="$1"; shift
DESCRIPTION="${1:-}"
LINEAR_CREATION_FLOW="${LINEAR_CREATION_FLOW:-}"
LINEAR_CREATION_AGENT="${OPENCLAW_AGENT_ID:-grok}"
LINEAR_DRAFT_ID="${LINEAR_DRAFT_ID:-}"

case "$LINEAR_CREATION_FLOW" in
  suggestion|user_request) ;;
  *)
    echo "LINEAR_CREATION_FLOW must be set to suggestion or user_request" >&2
    exit 1
    ;;
esac

[ -n "$LINEAR_DRAFT_ID" ] || {
  echo "LINEAR_DRAFT_ID must be set to an approved pending draft" >&2
  exit 1
}

PENDING_DRAFT_FILE="$WORKSPACE_ROOT/data/pending-linear-draft-${LINEAR_DRAFT_ID}.json"
[ -f "$PENDING_DRAFT_FILE" ] || {
  echo "approved draft not found: $PENDING_DRAFT_FILE" >&2
  exit 1
}

export LINEAR_PENDING_DRAFT_FILE="$PENDING_DRAFT_FILE"
export LINEAR_EXPECTED_FLOW="$LINEAR_CREATION_FLOW"
export LINEAR_EXPECTED_REFERENCE_ID="$REFERENCE_ID"
export LINEAR_EXPECTED_TITLE="$TITLE"
export LINEAR_EXPECTED_DESCRIPTION="$DESCRIPTION"
python3 <<'PY'
import json
import os
import sys

with open(os.environ["LINEAR_PENDING_DRAFT_FILE"], encoding="utf-8") as handle:
    draft = json.load(handle)

expected = {
    "flow": os.environ["LINEAR_EXPECTED_FLOW"],
    "referenceId": os.environ["LINEAR_EXPECTED_REFERENCE_ID"],
    "title": os.environ["LINEAR_EXPECTED_TITLE"],
    "description": os.environ["LINEAR_EXPECTED_DESCRIPTION"],
}

for key, value in expected.items():
    if draft.get(key, "") != value:
        print(f"approved draft mismatch for {key}", file=sys.stderr)
        sys.exit(1)
PY

OUTPUT=$(python3 "$WORKSPACE_ROOT/tools/_linear_ticket.py" \
  "$LINEAR_API_KEY" \
  "$REFERENCE_ID" \
  "$TITLE" \
  "$DESCRIPTION")

LINEAR_URL=$(printf '%s\n' "$OUTPUT" | tail -n1)
LOG_DIR="$WORKSPACE_ROOT/data/linear-creations"
LOG_FILE="$LOG_DIR/$(date -u +%Y-%m-%d).jsonl"
mkdir -p "$LOG_DIR"

LINEAR_LOG_FLOW="$LINEAR_CREATION_FLOW" \
LINEAR_LOG_REFERENCE_ID="$REFERENCE_ID" \
LINEAR_LOG_TITLE="$TITLE" \
LINEAR_LOG_URL="$LINEAR_URL" \
LINEAR_LOG_AGENT="$LINEAR_CREATION_AGENT" \
LINEAR_LOG_FILE="$LOG_FILE" \
python3 <<'PY'
import datetime
import json
import os

record = {
    "ts": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "flow": os.environ["LINEAR_LOG_FLOW"],
    "referenceId": os.environ["LINEAR_LOG_REFERENCE_ID"],
    "title": os.environ["LINEAR_LOG_TITLE"],
    "url": os.environ["LINEAR_LOG_URL"],
    "agent": os.environ["LINEAR_LOG_AGENT"],
}

with open(os.environ["LINEAR_LOG_FILE"], "a", encoding="utf-8") as handle:
    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
PY

printf '%s\n' "$OUTPUT"

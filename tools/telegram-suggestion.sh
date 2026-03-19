#!/bin/sh
# Post a daily suggestion with an Approve button.
# Usage: telegram-suggestion.sh <N> "<title>" "<reasoning>" "<impact>" "<description>"
#
# Writes data/pending-suggestion-N.json for dispatch-telegram-action.sh (approve_suggestion:N).
# Posts to suggestions topic with inline Approve button.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ "$#" -lt 5 ]; then
  echo "usage: $0 <N> \"<title>\" \"<reasoning>\" \"<impact>\" \"<description>\"" >&2
  exit 1
fi

N="$1"
TITLE="$2"
REASONING="$3"
IMPACT="$4"
DESCRIPTION="$5"

mkdir -p "$WORKSPACE_ROOT/data"
PENDING_FILE="$WORKSPACE_ROOT/data/pending-suggestion-${N}.json"
python3 -c "
import json, sys
with open(sys.argv[1], 'w') as f:
    json.dump({'title': sys.argv[2], 'description': sys.argv[3]}, f)
" "$PENDING_FILE" "$TITLE" "$DESCRIPTION"

MESSAGE="Daily Suggestion #${N}: ${TITLE}

Reasoning: ${REASONING}
Expected impact: ${IMPACT}

Tap Approve below."
BUTTON_JSON="[{\"text\":\"Approve\",\"callback_data\":\"approve_suggestion:${N}\"}]"

"$WORKSPACE_ROOT/tools/telegram-inline.sh" suggestions "$MESSAGE" "$BUTTON_JSON" "plain"

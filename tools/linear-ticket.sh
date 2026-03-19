#!/bin/sh
# Create a Linear ticket for an approved Grok suggestion.
# Usage: linear-ticket.sh <suggestion-number> <title> [description]
#
# Description is the PM-quality ticket body written by Grok.
# Always delegates to the Cursor agent.
# Prints the Linear issue URL on success.
# Env:   WORKSPACE_ROOT — workspace root (default: derived from script path)
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
  echo "usage: $0 <suggestion-number> <title> [description]" >&2
  exit 1
fi

SUGGESTION_NUMBER="$1"; shift
SUGGESTION_TITLE="$1"; shift
DESCRIPTION="${1:-}"

python3 "$WORKSPACE_ROOT/tools/_linear_ticket.py" \
  "$LINEAR_API_KEY" \
  "$SUGGESTION_NUMBER" \
  "$SUGGESTION_TITLE" \
  "$DESCRIPTION"

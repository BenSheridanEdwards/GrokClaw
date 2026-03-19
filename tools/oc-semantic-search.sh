#!/bin/sh
# Semantic search wrapper: query + context for Grok workflow.
# Usage: oc-semantic-search.sh "query" [--limit N]
# Calls opencv-copilot search and formats output for PR reviews, memory gaps.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ "$#" -lt 1 ]; then
  echo "usage: oc-semantic-search.sh \"query\" [--limit N]" >&2
  exit 1
fi

export WORKSPACE_ROOT
exec "$SCRIPT_DIR/opencv-copilot" search "$@"

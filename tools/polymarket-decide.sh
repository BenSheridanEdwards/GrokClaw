#!/bin/sh
# Polymarket decision engine: evaluate Grok's estimate against hard risk gates.
# Usage:
#   polymarket-decide.sh SKIP <reasoning>
#   polymarket-decide.sh <side> <probability> <confidence> <reasoning>
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ "$#" -lt 2 ]; then
  echo "usage: $0 SKIP <reasoning>" >&2
  echo "   or: $0 <side> <probability> <confidence> <reasoning>" >&2
  exit 1
fi

exec python3 "$SCRIPT_DIR/_polymarket_decide.py" "$WORKSPACE_ROOT" "$@"

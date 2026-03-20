#!/bin/sh
# Resolve Sentient paper trades against Manifold API.
# Usage: sentient-resolve.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec python3 "$SCRIPT_DIR/_sentient_resolve.py" "$WORKSPACE_ROOT"

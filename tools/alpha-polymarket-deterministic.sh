#!/bin/sh
# Deterministic Alpha hourly workflow executor.
# Usage:
#   alpha-polymarket-deterministic.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

python3 "$SCRIPT_DIR/_alpha_polymarket_deterministic.py" "$WORKSPACE_ROOT"

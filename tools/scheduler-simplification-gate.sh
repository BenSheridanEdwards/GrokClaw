#!/bin/sh
# 30-day scheduler simplification decision gate.
# Usage:
#   ./tools/scheduler-simplification-gate.sh [--date YYYY-MM-DD] [--days 30] [--json]
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/_scheduler_simplification_gate.py" "$@"

#!/bin/sh
# Consolidated operator truth view.
# Usage:
#   ./tools/cto-status.sh [--date YYYY-MM-DD] [--days N] [--json] [--offline]
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/_cto_status.py" "$@"

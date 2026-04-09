#!/bin/sh
# Generate baseline CTO reliability/economics KPIs.
# Usage:
#   ./tools/cto-kpi-report.sh [--date YYYY-MM-DD] [--days N] [--json]
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/_cto_kpi_report.py" "$@"

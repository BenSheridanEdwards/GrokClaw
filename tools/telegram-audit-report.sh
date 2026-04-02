#!/bin/sh
# Generate a Telegram audit summary with clarity flags.
# Usage:
#   telegram-audit-report.sh [--date YYYY-MM-DD] [--days N] [--limit N]
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

exec python3 "$SCRIPT_DIR/_telegram_audit_report.py" "$@"

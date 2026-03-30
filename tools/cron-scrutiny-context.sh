#!/bin/sh
# Print aggregated cron run data for Grok (grok-cron-scrutiny job). Read-only.
set -eu
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/_cron_scrutiny_context.py"

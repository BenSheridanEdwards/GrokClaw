#!/bin/sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

cd "$WORKSPACE_ROOT"

python3 -m unittest \
  tests.test_health_check \
  tests.test_gateway_watchdog \
  tests.test_health_schedules \
  tests.test_workflow_health \
  tests.test_grokclaw_doctor \
  tests.test_cron_paperclip_lifecycle \
  tests.test_telegram_audit_log

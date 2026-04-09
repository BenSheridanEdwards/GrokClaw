#!/bin/sh
# Post-run evidence contract enforcer for core workflows.
# Usage:
#   cron-workflow-evidence.sh <job> <agent> [run_id]
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

JOB="${1:?usage: cron-workflow-evidence.sh <job> <agent> [run_id]}"
AGENT="${2:?usage: cron-workflow-evidence.sh <job> <agent> [run_id]}"
RUN_ID="${3:-${CRON_RUN_ID:-}}"

if [ -n "$RUN_ID" ]; then
  python3 "$SCRIPT_DIR/_cron_workflow_evidence.py" "$JOB" "$AGENT" "$RUN_ID"
else
  python3 "$SCRIPT_DIR/_cron_workflow_evidence.py" "$JOB" "$AGENT"
fi

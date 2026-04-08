#!/bin/sh
# Clean up cron-run JSONL orphans, workflow-health Linear noise, and local state.
#
# Usage:
#   ./tools/grokclaw-maintenance.sh cron-runs [--apply] [--grace-hours N] [--now UTC]
#   ./tools/grokclaw-maintenance.sh linear-workflow-health [--apply] [--skip-linear|--skip-drafts|--skip-state]
#
# Loads .env for LINEAR_API_KEY when running linear-workflow-health.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [ "$#" -lt 1 ]; then
  echo "usage: $0 cron-runs [--apply] ... | linear-workflow-health [--apply] ..." >&2
  exit 1
fi

cmd="$1"
shift

case "$cmd" in
  cron-runs)
    exec python3 "$WORKSPACE_ROOT/tools/_cron_runs_cleanup.py" "$@"
    ;;
  linear-workflow-health)
    if [ -f "$WORKSPACE_ROOT/.env" ]; then
      set -a
      # shellcheck disable=SC1091
      . "$WORKSPACE_ROOT/.env"
      set +a
    fi
    exec python3 "$WORKSPACE_ROOT/tools/_linear_workflow_health_cleanup.py" "$@"
    ;;
  *)
    echo "unknown command: $cmd" >&2
    exit 1
    ;;
esac

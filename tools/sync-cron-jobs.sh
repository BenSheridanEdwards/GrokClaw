#!/bin/sh
# Validate repo cron/jobs.json, merge scheduler state from ~/.openclaw, write target, optional gateway restart.
# Usage:
#   sync-cron-jobs.sh              # write ~/.openclaw/cron/jobs.json
#   sync-cron-jobs.sh --restart    # same + gateway-ctl restart
#   sync-cron-jobs.sh --dry-run
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
RESTART=0
DRY=0
for arg in "$@"; do
  case "$arg" in
    --restart) RESTART=1 ;;
    --dry-run) DRY=1 ;;
  esac
done

extra=""
[ "$DRY" -eq 1 ] && extra="--dry-run"

if ! python3 "$WORKSPACE_ROOT/tools/cron-jobs-tool.py" sync $extra; then
  exit 1
fi

if [ "$DRY" -eq 1 ] || [ "$RESTART" -eq 0 ]; then
  exit 0
fi

"$WORKSPACE_ROOT/tools/gateway-ctl.sh" restart
echo "Gateway restarted to load cron jobs."

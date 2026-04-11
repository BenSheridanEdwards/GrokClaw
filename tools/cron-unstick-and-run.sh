#!/bin/sh
# Clear zombie `runningAtMs`, pause **all** core cron jobs so the scheduler does not
# immediately start due runs after gateway restart, restart gateway, enqueue manual runs,
# then re-enable the core jobs.
#
# Usage:
#   ./tools/cron-unstick-and-run.sh <job-id> [<job-id>...]
# Example:
#   ./tools/cron-unstick-and-run.sh 9c1b0a7d4e2f1003 9c1b0a7d4e2f1001
#
# Core job IDs match ~/.openclaw/cron/jobs.json (grok-daily-brief, alpha-polymarket).
# Env: OPENCLAW_CONFIG_PATH (default ~/.openclaw/openclaw.json)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
export OPENCLAW_CONFIG_PATH="${OPENCLAW_CONFIG_PATH:-${HOME}/.openclaw/openclaw.json}"

# grok-daily-brief, alpha-polymarket
CORE_CRON_IDS="9c1b0a7d4e2f1001 9c1b0a7d4e2f1003"

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <openclaw-cron-job-id> [<id>...]" >&2
  exit 1
fi

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

oc() {
  openclaw "$@" --timeout 120000
}

echo "cron-unstick-and-run: disabling core jobs (avoid auto-fire after restart)..."
for id in $CORE_CRON_IDS; do
  oc cron disable "$id" || true
done

python3 "$WORKSPACE_ROOT/tools/_cron_unstick_running.py" || exit 1
"$WORKSPACE_ROOT/tools/gateway-ctl.sh" restart

echo "cron-unstick-and-run: waiting for gateway health..."
i=0
while [ "$i" -lt 30 ]; do
  if curl -sf --connect-timeout 2 "http://127.0.0.1:$("$WORKSPACE_ROOT/tools/gateway-port.sh")/health" >/dev/null 2>&1; then
    echo "cron-unstick-and-run: gateway up"
    break
  fi
  i=$((i + 1))
  sleep 2
done
if [ "$i" -ge 30 ]; then
  echo "cron-unstick-and-run: gateway did not become healthy in time" >&2
  exit 1
fi

sleep 4

for id in "$@"; do
  echo "cron-unstick-and-run: enqueue $id"
  oc cron run "$id" || exit 1
done

echo "cron-unstick-and-run: re-enabling core jobs..."
for id in $CORE_CRON_IDS; do
  oc cron enable "$id" || true
done

echo "cron-unstick-and-run: done (runs execute in background; check data/cron-runs/ and Paperclip)"

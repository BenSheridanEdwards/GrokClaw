#!/bin/sh
# Print OpenClaw gateway HTTP port for health probes.
# Order: OPENCLAW_GATEWAY_PORT env, then gateway.port in OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json, else 18800.
set -eu

if [ -n "${OPENCLAW_GATEWAY_PORT:-}" ]; then
  printf '%s\n' "$OPENCLAW_GATEWAY_PORT"
  exit 0
fi

CONFIG="${OPENCLAW_CONFIG_PATH:-${HOME:-}/.openclaw/openclaw.json}"
if [ -f "$CONFIG" ]; then
  port=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('gateway',{}).get('port',18800))" "$CONFIG" 2>/dev/null) || port=""
  if [ -n "$port" ]; then
    printf '%s\n' "$port"
    exit 0
  fi
fi

printf '%s\n' "18800"

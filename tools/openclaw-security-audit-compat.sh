#!/bin/sh
# Run `openclaw security audit` when the CLI exists; no-op otherwise (CI / fresh boxes).
set -eu
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if command -v openclaw >/dev/null 2>&1; then
  exec openclaw security audit "$@"
fi
# Common macOS install path from polymarket-daily-turn.sh
if [ -x /opt/homebrew/bin/openclaw ]; then
  exec /opt/homebrew/bin/openclaw security audit "$@"
fi
echo "openclaw-security-audit-compat: openclaw not found, skip" >&2
exit 0

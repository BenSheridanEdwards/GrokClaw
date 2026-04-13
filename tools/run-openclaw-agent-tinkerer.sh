#!/usr/bin/env bash
# Run OpenClaw agent using the Tinkerer agent shell.
# Uses same Paperclip wake flow as run-openclaw-agent.sh but routes to the tinkerer agent.
set -euo pipefail

export OPENCLAW_AGENT_ID="tinkerer"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/run-openclaw-agent.sh"

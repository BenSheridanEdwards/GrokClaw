#!/usr/bin/env bash
# Run OpenClaw agent using Kimi K2.5 (ollama/kimi-k2.5).
# Uses same Paperclip wake flow as run-openclaw-agent.sh but routes to the kimi agent.
set -euo pipefail

export OPENCLAW_AGENT_ID="kimi"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/run-openclaw-agent.sh"

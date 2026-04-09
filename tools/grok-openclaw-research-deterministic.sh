#!/bin/sh
# Deterministic OpenClaw research workflow executor.
# Usage:
#   grok-openclaw-research-deterministic.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

python3 "$SCRIPT_DIR/_grok_openclaw_research_deterministic.py" "$WORKSPACE_ROOT"

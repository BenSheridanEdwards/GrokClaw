#!/bin/sh
# Alias for the deterministic Polymarket smoke test.
# Usage: polymarket-dry-run.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/polymarket-smoke.sh"

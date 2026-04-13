#!/bin/sh
# Launch the Tinkerer application agent.
# Usage:
#   ./tools/run-tinkerer-apply.sh --safe      # generate answers, no browser
#   ./tools/run-tinkerer-apply.sh --trial     # headed browser, live form, test placeholders, no Submit
#   ./tools/run-tinkerer-apply.sh --submit    # fill form with real data, prompt before submitting
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source .env for API keys
if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

# browser-use Python env has browser_use + langchain-openai installed
BROWSER_USE_PYTHON="$HOME/.browser-use-env/bin/python"
if [ -x "$BROWSER_USE_PYTHON" ]; then
  exec "$BROWSER_USE_PYTHON" "$SCRIPT_DIR/tinkerer-apply.py" --workspace "$WORKSPACE_ROOT" "$@"
else
  exec python3 "$SCRIPT_DIR/tinkerer-apply.py" --workspace "$WORKSPACE_ROOT" "$@"
fi

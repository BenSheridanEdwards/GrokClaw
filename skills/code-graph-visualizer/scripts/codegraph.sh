#!/bin/sh
# Thin wrapper: run workspace codegraph. Use from workspace root:
#   ./tools/codegraph.sh /path/to/repo --output graph.html
# When skill is loaded, WORKSPACE_ROOT may be set.
ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}"
exec "$ROOT/tools/codegraph.sh" "$@"

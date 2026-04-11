#!/bin/sh
# Rebuild graphify-out/ (graph.json, wiki, GRAPH_REPORT.md) from the repo root.
# Requires the Graphify Python package: https://github.com/BenSheridanEdwards/graphify
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

run_rebuild() {
  python3 -c "
from pathlib import Path
from graphify.watch import _rebuild_code
_rebuild_code(Path('.'))
"
}

if command -v python3 >/dev/null 2>&1; then
  if python3 -c "from graphify.watch import _rebuild_code" 2>/dev/null; then
    run_rebuild
    echo "graphify-rebuild: OK (python3 on PATH)"
    exit 0
  fi
fi

try_with_pythonpath() {
  dir="$1"
  [ -d "$dir" ] || return 1
  (
    PYTHONPATH="$dir${PYTHONPATH:+:$PYTHONPATH}"
    export PYTHONPATH
    cd "$ROOT"
    python3 -c "from graphify.watch import _rebuild_code" 2>/dev/null || exit 1
    python3 -c "
from pathlib import Path
from graphify.watch import _rebuild_code
_rebuild_code(Path('.'))
"
  ) || return 1
  echo "graphify-rebuild: OK (PYTHONPATH includes $dir)"
  exit 0
}

if [ -n "${GRAPHIFY_SRC:-}" ]; then
  try_with_pythonpath "$GRAPHIFY_SRC" || true
fi
try_with_pythonpath "$ROOT/../graphify" || true
try_with_pythonpath "${HOME}/src/graphify" || true
try_with_pythonpath "${HOME}/Projects/graphify" || true
try_with_pythonpath "${HOME}/Engineering/graphify" || true

cat >&2 <<'EOF'
graphify-rebuild: could not import graphify.watch._rebuild_code.

Install Graphify, then either:

  pip install --user -e /path/to/graphify-repo

or point GRAPHIFY_SRC at the repository root (the directory that contains the
`graphify` Python package):

  export GRAPHIFY_SRC=/path/to/graphify-repo
  ./tools/graphify-rebuild.sh

See README.md → Knowledge Graph.
EOF
exit 1

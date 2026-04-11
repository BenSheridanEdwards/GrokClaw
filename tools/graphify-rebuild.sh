#!/usr/bin/env bash
# Rebuild graphify-out/ (graph.json, wiki, GRAPH_REPORT.md) from the repo root.
# Requires the Graphify Python package: https://github.com/BenSheridanEdwards/graphify
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

try_rebuild() {
  local py="${1:-python3}"
  "$py" -c "
from pathlib import Path
from graphify.watch import _rebuild_code
_rebuild_code(Path('.'))
"
}

if command -v python3 >/dev/null 2>&1; then
  if python3 -c "from graphify.watch import _rebuild_code" 2>/dev/null; then
    try_rebuild python3
    echo "graphify-rebuild: OK (python3 on PATH)"
    exit 0
  fi
fi

candidates=()
if [[ -n "${GRAPHIFY_SRC:-}" ]]; then
  candidates+=("$GRAPHIFY_SRC")
fi
if [[ -d "$ROOT/../graphify" ]]; then
  candidates+=("$ROOT/../graphify")
fi
if [[ -d "${HOME}/src/graphify" ]]; then
  candidates+=("${HOME}/src/graphify")
fi
if [[ -d "${HOME}/Projects/graphify" ]]; then
  candidates+=("${HOME}/Projects/graphify")
fi
if [[ -d "${HOME}/Engineering/graphify" ]]; then
  candidates+=("${HOME}/Engineering/graphify")
fi

if ((${#candidates[@]} > 0)); then
  for dir in "${candidates[@]}"; do
    [[ -d "$dir" ]] || continue
    export PYTHONPATH="${dir}${PYTHONPATH:+:${PYTHONPATH}}"
    if python3 -c "from graphify.watch import _rebuild_code" 2>/dev/null; then
      try_rebuild python3
      echo "graphify-rebuild: OK (PYTHONPATH includes ${dir})"
      exit 0
    fi
  done
fi

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

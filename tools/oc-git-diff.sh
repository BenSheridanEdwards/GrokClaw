#!/bin/sh
# Structured git diff for branch comparison. For PR reviews, memory recall.
# Usage: oc-git-diff.sh [branch]
# Default branch: main. Output: structured changes (files, stats, diff summary).
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
cd "$WORKSPACE_ROOT"

BASE="${1:-main}"

echo "=== Structured diff: HEAD vs $BASE ==="
echo ""

echo "--- Changed files ---"
git diff --name-status "$BASE" HEAD 2>/dev/null || git diff --name-status "$BASE" 2>/dev/null

echo ""
echo "--- Stats ---"
git diff --stat "$BASE" HEAD 2>/dev/null || git diff --stat "$BASE" 2>/dev/null

echo ""
echo "--- Diff (first 300 lines) ---"
git diff "$BASE" HEAD 2>/dev/null | head -300 || git diff "$BASE" 2>/dev/null | head -300

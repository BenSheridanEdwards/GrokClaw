#!/bin/sh
# Output superpowers instructions for Cursor sessions.
# Usage: cursor-superpowers.sh [task-text]
#
# When delegating to Cursor (Linear ticket, PR, or ACP session), prepend this
# output so Cursor receives the superpowers workflow context.
#
# For OpenClaw sessions_spawn (when ACP runtime is stable):
#   sessions_spawn runtime=acp agentId=cursor task="$(./tools/cursor-superpowers.sh; echo; cat task.txt)"
#
# For create-pr.sh: PR body auto-injects superpowers via this script.
#
# Env: WORKSPACE_ROOT — workspace root (default: derived from script path)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
SKILL="$WORKSPACE_ROOT/skills/superpowers/SKILL.md"

if [ ! -f "$SKILL" ]; then
  echo "Error: skills/superpowers/SKILL.md not found" >&2
  exit 1
fi

# Output superpowers preamble
echo "## Superpowers workflow (mandatory)"
echo ""
echo "Read \`skills/superpowers/SKILL.md\` before starting. Follow: brainstorm → plan → TDD tasks → subagent exec → review."
echo ""
echo "**Core rules:**"
echo "- No production code without a failing test first (TDD)"
echo "- Break work into bite-sized tasks (2–5 min each)"
echo "- Review after each task and before merge"
echo ""

# Append task if provided
if [ "$#" -gt 0 ]; then
  echo "---"
  echo ""
  printf '%s\n' "$*"
fi

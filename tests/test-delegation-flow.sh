#!/usr/bin/env bash
# Test full delegation flow: Grok suggestion → approve → Linear ticket creation
#
# The delegation flow:
# 1. Grok posts a daily suggestion (Daily Suggestion #N: [title]...)
# 2. User replies exactly "approve"
# 3. Grok does NOT implement; instead delegates to Linear
# 4. Grok runs tools/linear-ticket.sh <number> <title> (or uses Linear MCP)
# 5. Grok replies in Slack with the ticket URL
#
# These tests verify the tooling and validation without requiring a real Linear API.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LINEAR_SCRIPT="$WORKSPACE_ROOT/tools/linear-ticket.sh"
TMUX_SCRIPTS="$WORKSPACE_ROOT/skills/tmux/scripts"

passed=0
failed=0

run_test() {
  local name="$1"
  local expected_exit="${2:-0}"
  shift 2
  set +e
  (cd "$WORKSPACE_ROOT" && "$@") 2>/tmp/delegation-test.err
  actual_exit=$?
  set -e
  if [ "$actual_exit" -eq "$expected_exit" ]; then
    echo "PASS: $name"
    ((passed++)) || true
    return 0
  else
    echo "FAIL: $name (expected exit $expected_exit, got $actual_exit)"
    [ -s /tmp/delegation-test.err ] && cat /tmp/delegation-test.err
    ((failed++)) || true
    return 1
  fi
}

run_test_output() {
  local name="$1"
  local pattern="$2"
  local expected_exit="${3:-0}"
  shift 3
  set +e
  output="$(cd "$WORKSPACE_ROOT" && "$@" 2>&1)"
  actual_exit=$?
  set -e
  if [ "$actual_exit" -eq "$expected_exit" ] && echo "$output" | grep -q -- "$pattern"; then
    echo "PASS: $name"
    ((passed++)) || true
    return 0
  else
    echo "FAIL: $name (exit=$actual_exit, pattern='$pattern')"
    echo "$output"
    ((failed++)) || true
    return 1
  fi
}

echo "=== Testing delegation flow tooling ==="

# linear-ticket.sh: missing args (usage goes to stderr)
run_test_output "linear-ticket.sh: no args shows usage" "usage:" 1 \
  env -i PATH="$PATH" "$LINEAR_SCRIPT"

run_test_output "linear-ticket.sh: one arg shows usage" "usage:" 1 \
  env -i PATH="$PATH" "$LINEAR_SCRIPT" "3"

# linear-ticket.sh: missing LINEAR_API_KEY
run_test_output "linear-ticket.sh: missing LINEAR_API_KEY fails clearly" "LINEAR_API_KEY is not configured" 1 \
  env -i PATH="$PATH" "$LINEAR_SCRIPT" "3" "test full delegation flow"

# linear-ticket.sh: with LINEAR_API_KEY but invalid (will fail at API, curl exits 22 for HTTP 401)
run_test "linear-ticket.sh: invalid API key fails at API" 22 \
  env -i PATH="$PATH" LINEAR_API_KEY="fake-key-for-test" LINEAR_TEAM_ID="3f1b1054-07c6-4aad-a02c-89c78a43946b" "$LINEAR_SCRIPT" "3" "test full delegation flow" 2>/dev/null

# tmux helper scripts: basic invocation
if [ -x "$TMUX_SCRIPTS/find-sessions.sh" ]; then
  run_test "find-sessions.sh: --help exits 0" 0 \
    "$TMUX_SCRIPTS/find-sessions.sh" --help
else
  echo "SKIP: find-sessions.sh not executable"
fi

if [ -x "$TMUX_SCRIPTS/wait-for-text.sh" ]; then
  run_test_output "wait-for-text.sh: missing args shows usage" "required" 1 \
    "$TMUX_SCRIPTS/wait-for-text.sh"
  # wait-for-text without -t -p should fail
  run_test "wait-for-text.sh: missing target/pattern fails" 1 \
    "$TMUX_SCRIPTS/wait-for-text.sh"
else
  echo "SKIP: wait-for-text.sh not executable"
fi

echo ""
echo "=== Results: $passed passed, $failed failed ==="
[ "$failed" -eq 0 ]

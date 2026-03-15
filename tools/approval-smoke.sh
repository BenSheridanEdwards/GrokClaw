#!/bin/sh
# Smoke test for the approval workflow. Validates approve-suggestion.sh logic.
# Usage: approval-smoke.sh
#
# Runs approve-suggestion.sh in dry-run mode and verifies it exits 0.
# Does not call Linear, GitHub, or Slack APIs.
# Env:   PICOCLAW_WORKSPACE — workspace root (default: derived from script path)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${PICOCLAW_WORKSPACE:-$(cd "$SCRIPT_DIR/.." && pwd)}"

echo "== Approval workflow smoke test =="
echo "Workspace: $WORKSPACE_ROOT"
echo ""

# Dry-run: validate args and step sequence
OUTPUT=$("$WORKSPACE_ROOT/tools/approve-suggestion.sh" --dry-run 8 "Test approval workflow reliability" "1234567890.123456" "Test description" 2>&1)
EXIT=$?

if [ "$EXIT" -ne 0 ]; then
  echo "FAIL: approve-suggestion.sh --dry-run exited $EXIT" >&2
  echo "$OUTPUT" >&2
  exit 1
fi

# Verify expected step sequence in output
if ! echo "$OUTPUT" | grep -q "linear-ticket.sh"; then
  echo "FAIL: output missing linear-ticket step" >&2
  echo "$OUTPUT" >&2
  exit 1
fi
if ! echo "$OUTPUT" | grep -q "create-pr.sh"; then
  echo "FAIL: output missing create-pr step" >&2
  echo "$OUTPUT" >&2
  exit 1
fi
if ! echo "$OUTPUT" | grep -q "slack-post.sh"; then
  echo "FAIL: output missing slack-post step" >&2
  echo "$OUTPUT" >&2
  exit 1
fi

echo "$OUTPUT"
echo ""
echo "PASS: Approval workflow dry-run completed successfully"

#!/bin/sh
# Smoke test for the approval workflow. Validates approve-suggestion.sh logic.
# Usage: approval-smoke.sh
#
# Runs approve-suggestion.sh in dry-run mode and verifies it exits 0.
# Does not call Linear, GitHub, or Telegram APIs.
# Env:   WORKSPACE_ROOT — workspace root (default: derived from script path)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

echo "== Approval workflow smoke test =="
echo "Workspace: $WORKSPACE_ROOT"
echo ""

# Dry-run: validate args and step sequence
OUTPUT=$("$WORKSPACE_ROOT/tools/approve-suggestion.sh" --dry-run 8 "Test approval workflow reliability" "suggestions" "Test description" 2>&1)
EXIT=$?

if [ "$EXIT" -ne 0 ]; then
  echo "FAIL: approve-suggestion.sh --dry-run exited $EXIT" >&2
  echo "$OUTPUT" >&2
  exit 1
fi

# Verify expected step sequence in output
case "$OUTPUT" in
  *"linear-draft-approval.sh request"*) ;;
  *)
    echo "FAIL: output missing linear draft approval step" >&2
    echo "$OUTPUT" >&2
    exit 1
    ;;
esac

case "$OUTPUT" in
  *"telegram-inline.sh"*) ;;
  *)
    echo "FAIL: output missing telegram-inline step" >&2
    echo "$OUTPUT" >&2
    exit 1
    ;;
esac

echo "$OUTPUT"
echo ""
echo "PASS: Approval workflow dry-run completed successfully"

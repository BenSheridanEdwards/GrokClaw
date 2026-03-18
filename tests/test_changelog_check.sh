#!/bin/sh
# Smoke test for changelog-check.sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$SCRIPT_DIR/.."
TOOLS="$WORKSPACE/tools"
DATA="$WORKSPACE/data"
STATE="$DATA/changelog-state.json"

# Create temp dir for fake picoclaw
TMP=$(mktemp -d)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

# Fake picoclaw that echoes version
echo '#!/bin/sh
echo "picoclaw 1.2.4"
' > "$TMP/picoclaw"
chmod +x "$TMP/picoclaw"
export PATH="$TMP:$PATH"

# Test 1: First run (no state) — should create state, no NEW_VERSION output
rm -f "$STATE"
out=$("$TOOLS/changelog-check.sh" 2>&1)
if echo "$out" | grep -q "NEW_VERSION"; then
  echo "FAIL: First run should not output NEW_VERSION"
  exit 1
fi
if [ ! -f "$STATE" ]; then
  echo "FAIL: State file should be created"
  exit 1
fi
echo "PASS: First run creates state, no new-version report"

# Test 2: Same version — should exit silently
echo '{"lastVersion":"1.2.4","lastCheckedAt":"2025-01-01T00:00:00Z"}' > "$STATE"
out=$("$TOOLS/changelog-check.sh" 2>&1)
if echo "$out" | grep -q "NEW_VERSION"; then
  echo "FAIL: Same version should not output NEW_VERSION"
  exit 1
fi
echo "PASS: Same version exits silently"

# Test 3: New version — should output NEW_VERSION_JSON
echo '{"lastVersion":"1.2.3","lastCheckedAt":"2025-01-01T00:00:00Z"}' > "$STATE"
out=$("$TOOLS/changelog-check.sh" 2>&1)
if ! echo "$out" | grep -q "NEW_VERSION_JSON:"; then
  echo "FAIL: New version should output NEW_VERSION_JSON"
  exit 1
fi
if ! echo "$out" | grep -qE '"new_version"[[:space:]]*:[[:space:]]*"1\.2\.4"'; then
  echo "FAIL: Output should contain new_version 1.2.4"
  exit 1
fi
if ! echo "$out" | grep -qE '"previous_version"[[:space:]]*:[[:space:]]*"1\.2\.3"'; then
  echo "FAIL: Output should contain previous_version 1.2.3"
  exit 1
fi
echo "PASS: New version outputs structured JSON"

echo "All changelog-check tests passed"

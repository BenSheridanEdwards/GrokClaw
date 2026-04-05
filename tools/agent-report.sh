#!/bin/sh
# Append an agent report for Grok to synthesize.
# Usage: agent-report.sh <agent> <job> <summary>
#   agent: alpha (or another explicitly targeted secondary worker)
#   job: job name (e.g. alpha-polymarket)
#   summary: report text (one line or use - to read from stdin)
#
# Reports go to data/agent-reports/YYYY-MM-DD.json
# Grok reads these for the daily brief.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
REPORTS_DIR="$WORKSPACE_ROOT/data/agent-reports"
DATE=$(date +%Y-%m-%d)
FILE="$REPORTS_DIR/$DATE.json"

[ "$#" -ge 3 ] || { echo "usage: agent-report.sh <agent> <job> <summary>" >&2; exit 1; }
AGENT="$1"
JOB="$2"
shift 2
if [ "${1:-}" = "-" ]; then
  SUMMARY=$(cat)
else
  SUMMARY="$*"
fi

mkdir -p "$REPORTS_DIR"

# Append to JSON array; init file if missing
if [ ! -f "$FILE" ]; then
  echo '{"reports":[]}' >"$FILE"
fi

# Append using Python for robust JSON handling
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
printf '%s' "$SUMMARY" >"$TMP"
python3 - "$FILE" "$AGENT" "$JOB" "$TMP" <<'PY'
import json, sys
path, agent, job, summary_path = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
with open(summary_path) as f:
    summary = f.read().strip()
ts = __import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
with open(path) as f:
    d = json.load(f)
d['reports'].append({'agent': agent, 'job': job, 'timestamp': ts, 'summary': summary})
with open(path, 'w') as f:
    json.dump(d, f, indent=2)
PY

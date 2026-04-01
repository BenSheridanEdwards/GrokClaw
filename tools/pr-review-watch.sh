#!/bin/sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
RUN_AGENT="$WORKSPACE_ROOT/tools/run-openclaw-agent.sh"
STATE_DIR="${HOME}/.openclaw/state"
STATE_FILE="$STATE_DIR/pr-review-watch.last"
REPO="${GROKCLAW_GITHUB_REPO:-BenSheridanEdwards/GrokClaw}"

mkdir -p "$STATE_DIR"

queue_json="$(gh pr list --repo "$REPO" --state open --label needs-grok-review --json number,title,url,headRefName,isDraft)"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

QUEUE_JSON="$queue_json" TMP_DIR="$tmp_dir" python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path

items = json.loads(os.environ["QUEUE_JSON"])
items = sorted(items, key=lambda item: item["number"])
tmp_dir = Path(os.environ["TMP_DIR"])

(tmp_dir / "count").write_text(str(len(items)), encoding="utf-8")

if not items:
    raise SystemExit(0)

payload = json.dumps(items, sort_keys=True, separators=(",", ":"))
digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
summary_lines = []
for item in items:
    title = " ".join((item.get("title") or "").split())
    summary_lines.append(f"#{item['number']} {title} ({item.get('url', '')})")

(tmp_dir / "digest").write_text(digest, encoding="utf-8")
(tmp_dir / "summary").write_text("\n".join(summary_lines), encoding="utf-8")
PY

count="$(cat "$tmp_dir/count")"

if [ "$count" = "0" ]; then
  rm -f "$STATE_FILE"
  exit 0
fi

digest="$(cat "$tmp_dir/digest")"
summary="$(cat "$tmp_dir/summary")"

if [ -f "$STATE_FILE" ] && [ "$(cat "$STATE_FILE")" = "$digest" ]; then
  exit 0
fi

printf '%s\n' "$digest" > "$STATE_FILE"

OPENCLAW_MESSAGE="You are Grok, the GrokClaw orchestration agent. Read AGENTS.md for your operating instructions.

There are pull requests waiting in the GitHub review queue with the label needs-grok-review.

Queued pull requests:
$summary

Review each queued PR against its linked Linear issue and current code. Use tools/pr-review-handler.sh list to confirm the queue, then either:
- approve <pr-number> <linear-issue-id> \"<telegram-summary>\" \"<review-body>\"
- request-changes <pr-number> \"<review-body>\"

Only send Telegram merge/reject buttons after GitHub approval is already recorded."

OPENCLAW_MESSAGE="$OPENCLAW_MESSAGE" "$RUN_AGENT"

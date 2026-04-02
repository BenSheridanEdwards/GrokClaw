#!/bin/sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

APPLY=0
if [ "${1:-}" = "--apply" ]; then
  APPLY=1
  shift
fi

if [ "$#" -ne 0 ]; then
  echo "usage: $0 [--apply]" >&2
  exit 1
fi

python3 - "$WORKSPACE_ROOT" "$APPLY" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
apply_mode = sys.argv[2] == "1"


def norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


data_dir = root / "data"
pending_files = sorted(data_dir.glob("pending-linear-draft-workflow-health-*.json"))

if not pending_files:
    print("No workflow-health pending draft files found.")
    raise SystemExit(0)

created_refs = set()
for log_file in sorted((data_dir / "linear-creations").glob("*.jsonl")):
    try:
        lines = log_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        continue
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("flow") != "suggestion":
            continue
        reference_id = str(event.get("referenceId", "")).strip()
        if reference_id:
            created_refs.add(reference_id)

records = []
for path in pending_files:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        payload = {}
    title = str(payload.get("title", "")).strip()
    ref = str(payload.get("referenceId", "")).strip()
    records.append(
        {
            "path": path,
            "title": title,
            "title_norm": norm(title),
            "referenceId": ref,
            "mtime": path.stat().st_mtime,
        }
    )

latest_by_title = {}
for record in records:
    key = record["title_norm"]
    if not key:
        continue
    current = latest_by_title.get(key)
    if current is None or record["mtime"] > current["mtime"]:
        latest_by_title[key] = record

stale = []
for record in records:
    reason = ""
    if record["referenceId"] and record["referenceId"] in created_refs:
        reason = "linear_ticket_already_created"
    elif record["title_norm"]:
        latest = latest_by_title.get(record["title_norm"])
        if latest and latest["path"] != record["path"]:
            reason = "superseded_by_newer_draft"
    if reason:
        stale.append((record, reason))

if not stale:
    print("No stale workflow-health pending drafts found.")
    raise SystemExit(0)

mode = "apply" if apply_mode else "dry-run"
print(f"Found {len(stale)} stale workflow-health pending draft file(s) ({mode}).")
for record, reason in stale:
    print(f"- {record['path'].name}: {reason}")

if not apply_mode:
    print("Dry run only. Re-run with --apply to delete these files.")
    raise SystemExit(0)

deleted = 0
for record, _ in stale:
    try:
        record["path"].unlink()
        deleted += 1
    except OSError:
        pass

print(f"Deleted {deleted} stale draft file(s).")
PY

#!/usr/bin/env python3
import datetime as dt
import json
import os
import sys
from pathlib import Path


def utc_now() -> dt.datetime:
    raw = os.environ.get("AUDIT_LOG_NOW") or os.environ.get("WORKFLOW_HEALTH_NOW")
    if raw:
        return dt.datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
    return dt.datetime.utcnow()


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: _audit_log.py <kind> <topic> <message> [topic-id]", file=sys.stderr)
        return 1

    kind = sys.argv[1]
    topic = sys.argv[2]
    message = sys.argv[3]
    topic_id = sys.argv[4] if len(sys.argv) > 4 else ""
    workspace_root = Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[1]))

    now = utc_now()
    directory = workspace_root / "data" / "audit-log"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{now.strftime('%Y-%m-%d')}.jsonl"

    record = {
        "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": kind,
        "topic": topic,
        "topicId": topic_id,
        "message": message,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

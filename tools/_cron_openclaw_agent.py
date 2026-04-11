#!/usr/bin/env python3
"""Run `openclaw agent` with message body read from a UTF-8 file (avoids shell quoting issues)."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import time
import subprocess
import sys
from pathlib import Path


def classify_failure(stdout: str, stderr: str, exit_code: int) -> str:
    combined = f"{stdout}\n{stderr}".lower()
    if exit_code == 124 or "timeout" in combined:
        return "timeout"
    if "rate limit" in combined or "429" in combined:
        return "rate_limit"
    if "unavailable" in combined or "503" in combined or "connection refused" in combined:
        return "provider_unavailable"
    if "auth" in combined or "token" in combined:
        return "auth"
    return "unknown"


def append_retry_telemetry(
    telemetry_file: Path | None,
    *,
    agent: str,
    session_id: str,
    attempt: int,
    max_attempts: int,
    exit_code: int,
    reason: str,
) -> None:
    if telemetry_file is None:
        return
    telemetry_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agent": agent,
        "sessionId": session_id,
        "attempt": attempt,
        "maxAttempts": max_attempts,
        "exitCode": exit_code,
        "reason": reason,
    }
    with telemetry_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt_file", type=Path, help="Path to UTF-8 prompt file")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--timeout", type=int, default=600, help="Timeout in seconds (openclaw --timeout)")
    parser.add_argument("--retries", type=int, default=0, help="Retry attempts after the first failure")
    parser.add_argument("--retry-backoff", type=int, default=1, help="Base backoff in seconds between retries")
    parser.add_argument("--telemetry-file", type=Path, default=None, help="Optional JSONL path for retry telemetry")
    parser.add_argument("--cwd", type=Path, required=True)
    args = parser.parse_args()

    text = args.prompt_file.read_text(encoding="utf-8")
    openclaw_bin = os.environ.get("OPENCLAW_BIN", "openclaw")
    cmd = [
        openclaw_bin,
        "agent",
        "--agent",
        args.agent,
        "--message",
        text,
        "--session-id",
        args.session_id,
        "--timeout",
        str(args.timeout),
    ]
    max_attempts = max(1, args.retries + 1)
    for attempt in range(1, max_attempts + 1):
        result = subprocess.run(
            cmd,
            cwd=str(args.cwd),
            capture_output=True,
            text=True,
        )
        if result.stdout:
            sys.stdout.write(result.stdout)
            sys.stdout.flush()
        if result.stderr:
            sys.stderr.write(result.stderr)
            sys.stderr.flush()

        if int(result.returncode) == 0:
            return 0

        reason = classify_failure(result.stdout or "", result.stderr or "", int(result.returncode))
        append_retry_telemetry(
            args.telemetry_file,
            agent=args.agent,
            session_id=args.session_id,
            attempt=attempt,
            max_attempts=max_attempts,
            exit_code=int(result.returncode),
            reason=reason,
        )
        if reason in ("auth",):
            return int(result.returncode)

        if attempt >= max_attempts:
            return int(result.returncode)

        wait_seconds = max(0, args.retry_backoff * (2 ** (attempt - 1)))
        if wait_seconds > 0:
            time.sleep(wait_seconds)
    return 1


if __name__ == "__main__":
    sys.exit(main())

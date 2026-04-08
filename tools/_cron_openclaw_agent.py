#!/usr/bin/env python3
"""Run `openclaw agent` with message body read from a UTF-8 file (avoids shell quoting issues)."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt_file", type=Path, help="Path to UTF-8 prompt file")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--timeout", type=int, default=600, help="Timeout in seconds (openclaw --timeout)")
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
    result = subprocess.run(cmd, cwd=str(args.cwd))
    return int(result.returncode)


if __name__ == "__main__":
    sys.exit(main())

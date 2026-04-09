#!/usr/bin/env python3
"""Alpha memory command entrypoint (MemPalace only)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[1]))
BACKEND_STATE = WORKSPACE_ROOT / "data" / "alpha" / "memory" / "backend.json"
BACKEND = "mempalace"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_backend_state(reason: str = "defaulted to mempalace") -> None:
    BACKEND_STATE.parent.mkdir(parents=True, exist_ok=True)
    BACKEND_STATE.write_text(
        json.dumps({"backend": BACKEND, "reason": reason, "updatedAt": now_iso()}, indent=2) + "\n",
        encoding="utf-8",
    )


def backend_script() -> Path:
    return WORKSPACE_ROOT / "tools" / "mempalace-alpha.py"


def run_backend(args: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    script = backend_script()
    if not script.exists():
        raise FileNotFoundError(f"Backend script missing: {script}")
    return subprocess.run(
        ["python3", str(script), *args],
        cwd=str(WORKSPACE_ROOT),
        capture_output=capture,
        text=True,
        check=False,
    )


def mempalace_health_check() -> tuple[bool, str]:
    try:
        recent = run_backend(["recent-trades"], capture=True)
        whale = run_backend(["whale-accuracy"], capture=True)
    except FileNotFoundError as exc:
        return False, str(exc)
    if recent.returncode != 0:
        return False, recent.stderr.strip() or recent.stdout.strip() or "recent-trades failed"
    if whale.returncode != 0:
        return False, whale.stderr.strip() or whale.stdout.strip() or "whale-accuracy failed"
    return True, "mempalace healthy"


USAGE = """
Usage:
  alpha-memory.py backend
  alpha-memory.py backend switch mempalace [reason]
  alpha-memory.py health-check
  alpha-memory.py <memory-command...>
"""


def main() -> int:
    if len(sys.argv) < 2:
        print(USAGE, file=sys.stderr)
        return 1

    cmd = sys.argv[1]
    if cmd == "backend":
        if len(sys.argv) == 2:
            ensure_backend_state("read backend")
            print(BACKEND)
            return 0
        if len(sys.argv) >= 4 and sys.argv[2] == "switch":
            backend = sys.argv[3].strip().lower()
            if backend != BACKEND:
                print("backend must be mempalace", file=sys.stderr)
                return 1
            reason = sys.argv[4] if len(sys.argv) >= 5 else "manual switch"
            ensure_backend_state(reason)
            print("Switched alpha memory backend to mempalace")
            return 0
        print(USAGE, file=sys.stderr)
        return 1

    if cmd == "health-check":
        ensure_backend_state("health-check")
        ok, reason = mempalace_health_check()
        if ok:
            print(reason)
            return 0
        print(reason, file=sys.stderr)
        return 1

    ensure_backend_state("command dispatch")
    proc = run_backend(sys.argv[1:])
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())

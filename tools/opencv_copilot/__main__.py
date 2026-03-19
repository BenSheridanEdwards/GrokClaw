#!/usr/bin/env python3
"""CLI entry for opencv-copilot. Usage: opencv-copilot search <query>"""
import os
import sys

# Ensure workspace root is in path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(TOOLS_DIR)
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from tools.opencv_copilot.search import main_search


def main():
    workspace = os.environ.get("WORKSPACE_ROOT", WORKSPACE_ROOT)
    if len(sys.argv) < 2:
        print("usage: opencv-copilot <search|index> [args...]", file=sys.stderr)
        print("  search <query> [--limit N]  semantic search", file=sys.stderr)
        sys.exit(1)
    sub = sys.argv[1].lower()
    if sub == "search":
        sys.exit(main_search(sys.argv[1:], workspace))
    print(f"unknown subcommand: {sub}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()

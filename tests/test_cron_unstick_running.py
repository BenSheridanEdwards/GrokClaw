"""Tests for tools/_cron_unstick_running.py."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import _cron_unstick_running as mod  # noqa: E402


class CronUnstickRunningTests(unittest.TestCase):
    def test_strip_removes_running_and_counts(self) -> None:
        data = {
            "version": 1,
            "jobs": [
                {"id": "1", "name": "a", "state": {"runningAtMs": 1, "nextRunAtMs": 2}},
                {"id": "2", "name": "b", "state": {"nextRunAtMs": 3}},
            ],
        }
        n, names = mod.strip_running_at_ms(data)
        self.assertEqual(n, 1)
        self.assertEqual(names, ["a"])
        self.assertNotIn("runningAtMs", data["jobs"][0]["state"])

    def test_strip_idempotent(self) -> None:
        data = {"jobs": [{"state": {}}]}
        self.assertEqual(mod.strip_running_at_ms(data), (0, []))


if __name__ == "__main__":
    unittest.main()

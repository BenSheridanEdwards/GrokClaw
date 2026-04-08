"""Tests for tools/_cron_runs_cleanup.py."""
from __future__ import annotations

import datetime as dt
import json
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import _cron_runs_cleanup as crc  # noqa: E402


class CronRunsCleanupTests(unittest.TestCase):
    def test_redundant_started_drops_earlier_only(self) -> None:
        lines = [
            '{"job": "alpha-polymarket", "status": "started", "ts": "2026-01-01T01:00:00Z"}',
            '{"job": "alpha-polymarket", "status": "started", "ts": "2026-01-01T01:01:00Z"}',
            '{"job": "alpha-polymarket", "status": "ok", "ts": "2026-01-01T01:02:00Z"}',
        ]
        drop = crc.redundant_started_indices_for_file(lines)
        self.assertEqual(drop, {0})

    def test_redundant_started_resets_after_terminal(self) -> None:
        lines = [
            '{"job": "j", "status": "started", "ts": "2026-01-01T01:00:00Z"}',
            '{"job": "j", "status": "ok", "ts": "2026-01-01T01:01:00Z"}',
            '{"job": "j", "status": "started", "ts": "2026-01-01T02:00:00Z"}',
        ]
        drop = crc.redundant_started_indices_for_file(lines)
        self.assertEqual(drop, set())

    def test_orphan_started_removes_stale_latest(self) -> None:
        records = [
            (
                Path("/x.jsonl"),
                0,
                {"job": "j", "status": "ok", "ts": "2026-01-01T00:00:00Z"},
            ),
            (
                Path("/x.jsonl"),
                1,
                {"job": "j", "status": "started", "ts": "2026-01-01T01:00:00Z"},
            ),
        ]
        now = dt.datetime(2026, 1, 1, 5, 0, 0, tzinfo=dt.timezone.utc)
        out = crc.orphan_started_indices(records, now, grace_hours=1.0)
        self.assertEqual(out, {(Path("/x.jsonl"), 1)})

    def test_orphan_started_not_removed_within_grace(self) -> None:
        records = [
            (Path("/x.jsonl"), 0, {"job": "j", "status": "started", "ts": "2026-01-01T04:30:00Z"}),
        ]
        now = dt.datetime(2026, 1, 1, 5, 0, 0, tzinfo=dt.timezone.utc)
        out = crc.orphan_started_indices(records, now, grace_hours=2.0)
        self.assertEqual(out, set())

    def test_plan_cleanup_integration(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cr = root / "data" / "cron-runs"
            cr.mkdir(parents=True)
            p = cr / "2026-01-02.jsonl"
            p.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "job": "grok-daily-brief",
                                "status": "started",
                                "ts": "2026-01-02T08:00:00Z",
                            }
                        ),
                        json.dumps(
                            {
                                "job": "grok-daily-brief",
                                "status": "started",
                                "ts": "2026-01-02T08:01:00Z",
                            }
                        ),
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            now = dt.datetime(2026, 1, 2, 12, 0, 0, tzinfo=dt.timezone.utc)
            actions = crc.plan_cleanup(root, now=now, grace_hours=1.0)
            reasons = {a.reason for a in actions}
            self.assertIn("duplicate_started", reasons)
            self.assertIn("orphan_started", reasons)
            crc.apply_line_removals(actions)
            kept = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
            self.assertEqual(len(kept), 0)


if __name__ == "__main__":
    unittest.main()

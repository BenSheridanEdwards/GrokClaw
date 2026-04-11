import importlib.util
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


def _load_audit_module():
    repo = Path(__file__).resolve().parents[1]
    path = repo / "tools" / "_workflow_health_audit.py"
    name = "grokclaw_workflow_health_audit_test"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class WorkflowHealthAuditTests(unittest.TestCase):
    def test_last_expected_fire_hourly_and_daily(self):
        wha = _load_audit_module()
        now = datetime(2026, 4, 1, 13, 30, tzinfo=timezone.utc)
        self.assertEqual(
            wha._last_expected_fire("0 * * * *", now).hour,
            13,
        )
        self.assertEqual(
            wha._last_expected_fire("0 8 * * *", now).day,
            1,
        )
        earlier = datetime(2026, 4, 1, 7, 30, tzinfo=timezone.utc)
        self.assertEqual(
            wha._last_expected_fire("0 8 * * *", earlier).day,
            31,
        )
        self.assertEqual(wha._last_expected_fire("0 8 * * *", earlier).month,
                         3)

    def test_audit_passes_when_records_in_window(self):
        import tempfile

        wha = _load_audit_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "cron").mkdir(parents=True)
            (root / "data" / "cron-runs").mkdir(parents=True)
            (root / "cron" / "jobs.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "jobs": [
                            {"name": "grok-daily-brief", "schedule": {"expr": "0 8 * * *"}},
                            {"name": "alpha-polymarket", "schedule": {"expr": "0 * * * *"}},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            day_file = root / "data" / "cron-runs" / "2026-04-01.jsonl"
            lines = [
                json.dumps(
                    {
                        "job": "grok-daily-brief",
                        "agent": "grok",
                        "ts": "2026-04-01T08:05:00Z",
                        "status": "ok",
                        "summary": "brief posted",
                    }
                ),
                json.dumps(
                    {
                        "job": "alpha-polymarket",
                        "agent": "alpha",
                        "ts": "2026-04-01T13:05:00Z",
                        "status": "ok",
                        "summary": "alpha ok",
                    }
                ),
            ]
            day_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

            # Before :00 of the next hour so the last hourly fire is 13:00 (records at 13:05 / 13:10 qualify).
            now = datetime(2026, 4, 1, 13, 45, tzinfo=timezone.utc)
            ok_msgs, fail_msgs = wha.audit(now=now, repo=root)
            self.assertEqual(fail_msgs, [])
            self.assertEqual(len(ok_msgs), 2)

    def test_audit_fails_when_hourly_missing(self):
        import tempfile

        wha = _load_audit_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "cron").mkdir(parents=True)
            (root / "data" / "cron-runs").mkdir(parents=True)
            (root / "cron" / "jobs.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "jobs": [
                            {"name": "grok-daily-brief", "schedule": {"expr": "0 8 * * *"}},
                            {"name": "alpha-polymarket", "schedule": {"expr": "0 * * * *"}},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            day_file = root / "data" / "cron-runs" / "2026-04-01.jsonl"
            lines = [
                json.dumps(
                    {
                        "job": "grok-daily-brief",
                        "agent": "grok",
                        "ts": "2026-04-01T08:05:00Z",
                        "status": "ok",
                        "summary": "brief",
                    }
                ),
                json.dumps(
                    {
                        "job": "alpha-polymarket",
                        "agent": "alpha",
                        "ts": "2026-04-01T13:05:00Z",
                        "status": "ok",
                        "summary": "alpha",
                    }
                ),
            ]
            day_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

            now = datetime(2026, 4, 1, 14, 0, tzinfo=timezone.utc)
            _ok, fail_msgs = wha.audit(now=now, repo=root)
            self.assertTrue(any("alpha-polymarket" in m for m in fail_msgs))


if __name__ == "__main__":
    unittest.main()

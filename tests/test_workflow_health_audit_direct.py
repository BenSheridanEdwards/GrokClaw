import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


def _load_audit_module():
    repo = Path(__file__).resolve().parents[1]
    path = repo / "tools" / "_workflow_health_audit.py"
    name = "grokclaw_workflow_health_audit_direct_test"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_minimal_repo(tmpdir):
    root = Path(tmpdir)
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
    return root


class WorkflowHealthAuditDirectTests(unittest.TestCase):
    """Direct unit tests for _workflow_health_audit.py audit() function."""

    def test_last_expected_fire_hourly_returns_current_hour_floor(self):
        wha = _load_audit_module()
        now = datetime(2026, 4, 1, 14, 32, 15, tzinfo=timezone.utc)
        result = wha._last_expected_fire("0 * * * *", now)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 0)
        self.assertEqual(result.second, 0)

    def test_last_expected_fire_daily_returns_today_if_passed(self):
        wha = _load_audit_module()
        now = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
        result = wha._last_expected_fire("0 8 * * *", now)
        self.assertEqual(result.day, 1)
        self.assertEqual(result.hour, 8)

    def test_last_expected_fire_daily_returns_prev_day_if_before(self):
        wha = _load_audit_module()
        now = datetime(2026, 4, 1, 7, 0, 0, tzinfo=timezone.utc)
        result = wha._last_expected_fire("0 8 * * *", now)
        self.assertEqual(result.day, 31)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.hour, 8)

    def test_last_expected_fire_raises_on_unsupported_expr(self):
        wha = _load_audit_module()
        now = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
        with self.assertRaises(ValueError) as ctx:
            wha._last_expected_fire("0 9 * * *", now)
        self.assertIn("unsupported schedule expr", str(ctx.exception))

    def test_grace_is_75min_for_hourly_120min_for_daily(self):
        wha = _load_audit_module()
        self.assertEqual(wha._grace_for_schedule("0 * * * *").total_seconds(), 75 * 60)
        self.assertEqual(wha._grace_for_schedule("0 8 * * *").total_seconds(), 120 * 60)

    def test_audit_returns_empty_failures_when_all_in_window(self):
        wha = _load_audit_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_minimal_repo(tmpdir)
            day_file = root / "data" / "cron-runs" / "2026-04-01.jsonl"
            day_file.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "job": "grok-daily-brief",
                                "ts": "2026-04-01T08:05:00Z",
                                "status": "ok",
                            }
                        ),
                        json.dumps(
                            {
                                "job": "alpha-polymarket",
                                "ts": "2026-04-01T13:05:00Z",
                                "status": "ok",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            now = datetime(2026, 4, 1, 13, 30, tzinfo=timezone.utc)
            ok_msgs, fail_msgs = wha.audit(now=now, repo=root)
            self.assertEqual(fail_msgs, [])
            self.assertEqual(len(ok_msgs), 2)

    def test_audit_fails_when_hourly_job_has_no_record(self):
        wha = _load_audit_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_minimal_repo(tmpdir)
            day_file = root / "data" / "cron-runs" / "2026-04-01.jsonl"
            day_file.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "job": "grok-daily-brief",
                                "ts": "2026-04-01T08:05:00Z",
                                "status": "ok",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            now = datetime(2026, 4, 1, 14, 30, tzinfo=timezone.utc)
            ok_msgs, fail_msgs = wha.audit(now=now, repo=root)
            self.assertTrue(any("alpha-polymarket" in m for m in fail_msgs))

    def test_audit_alpha_passes_with_record_in_window(self):
        wha = _load_audit_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_minimal_repo(tmpdir)
            day_file = root / "data" / "cron-runs" / "2026-04-01.jsonl"
            day_file.write_text(
                json.dumps(
                    {
                        "job": "alpha-polymarket",
                        "ts": "2026-04-01T10:05:00Z",
                        "status": "ok",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            now = datetime(2026, 4, 1, 10, 30, tzinfo=timezone.utc)
            ok_msgs, fail_msgs = wha.audit(now=now, repo=root)
            alpha_fail = [m for m in fail_msgs if "alpha-polymarket" in m]
            self.assertEqual(alpha_fail, [], msg=f"alpha should pass: {alpha_fail}")

    def test_audit_skips_records_outside_grace_window(self):
        wha = _load_audit_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_minimal_repo(tmpdir)
            day_file = root / "data" / "cron-runs" / "2026-04-01.jsonl"
            day_file.write_text(
                json.dumps(
                    {
                        "job": "grok-daily-brief",
                        "ts": "2026-04-01T06:00:00Z",
                        "status": "ok",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            now = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
            ok_msgs, fail_msgs = wha.audit(now=now, repo=root)
            self.assertTrue(
                any(
                    "grok-daily-brief" in m and "no cron-run-record" in m
                    for m in fail_msgs
                )
            )

    def test_audit_window_boundary_record_passes(self):
        wha = _load_audit_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_minimal_repo(tmpdir)
            day_file = root / "data" / "cron-runs" / "2026-04-01.jsonl"
            day_file.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "job": "grok-daily-brief",
                                "ts": "2026-04-01T08:05:00Z",
                                "status": "ok",
                            }
                        ),
                        json.dumps(
                            {
                                "job": "alpha-polymarket",
                                "ts": "2026-04-01T14:15:00Z",
                                "status": "ok",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            now = datetime(2026, 4, 1, 14, 15, tzinfo=timezone.utc)
            ok_msgs, fail_msgs = wha.audit(now=now, repo=root)
            alpha_fail = [m for m in fail_msgs if "alpha-polymarket" in m]
            self.assertEqual(
                alpha_fail,
                [],
                msg=f"alpha at window boundary should pass: {alpha_fail}",
            )

    def test_records_for_job_reads_across_two_day_files(self):
        wha = _load_audit_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "data" / "cron-runs").mkdir(parents=True)
            f1 = root / "data" / "cron-runs" / "2026-04-01.jsonl"
            f1.write_text(
                json.dumps(
                    {
                        "job": "alpha-polymarket",
                        "ts": "2026-04-01T23:05:00Z",
                        "status": "ok",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            f2 = root / "data" / "cron-runs" / "2026-04-02.jsonl"
            f2.write_text(
                json.dumps(
                    {
                        "job": "alpha-polymarket",
                        "ts": "2026-04-02T00:05:00Z",
                        "status": "ok",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            paths = wha._read_jsonl_paths(
                root, datetime(2026, 4, 2, 1, 0, tzinfo=timezone.utc)
            )
            recs = wha._records_for_job(paths, "alpha-polymarket")
            self.assertEqual(len(recs), 2)

    def test_records_for_job_skips_malformed_lines(self):
        wha = _load_audit_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "data" / "cron-runs").mkdir(parents=True)
            f = root / "data" / "cron-runs" / "2026-04-01.jsonl"
            f.write_text(
                json.dumps(
                    {
                        "job": "alpha-polymarket",
                        "ts": "2026-04-01T13:05:00Z",
                        "status": "ok",
                    }
                )
                + "\n"
                + "not valid json\n"
                + json.dumps(
                    {
                        "job": "alpha-polymarket",
                        "ts": "2026-04-01T14:05:00Z",
                        "status": "ok",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            paths = wha._read_jsonl_paths(
                root, datetime(2026, 4, 1, 15, 0, tzinfo=timezone.utc)
            )
            recs = wha._records_for_job(paths, "alpha-polymarket")
            self.assertEqual(len(recs), 2)

    def test_records_for_job_handles_missing_day_files(self):
        wha = _load_audit_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "data" / "cron-runs").mkdir(parents=True)
            paths = wha._read_jsonl_paths(
                root, datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
            )
            recs = wha._records_for_job(paths, "alpha-polymarket")
            self.assertEqual(recs, [])

    def test_load_cron_jobs_parses_all_two_core_workflows(self):
        wha = _load_audit_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_minimal_repo(tmpdir)
            jobs = wha._load_cron_jobs(root)
            self.assertIn("grok-daily-brief", jobs)
            self.assertIn("alpha-polymarket", jobs)
            self.assertEqual(jobs["grok-daily-brief"].schedule_expr, "0 8 * * *")
            self.assertEqual(jobs["alpha-polymarket"].schedule_expr, "0 * * * *")


if __name__ == "__main__":
    unittest.main()

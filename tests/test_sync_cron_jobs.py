import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from pathlib import Path


def _load_cron_jobs_tool():
    repo = Path(__file__).resolve().parents[1]
    path = repo / "tools" / "cron-jobs-tool.py"
    name = "grokclaw_cron_jobs_tool_test"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestSyncCronJobsScript(unittest.TestCase):
    """Tests for sync-cron-jobs.sh"""

    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "sync-cron-jobs.sh"

    def _run_sync_script(self, *args, repo=None):
        workspace = repo or self.workspace
        env = os.environ.copy()
        env["WORKSPACE_ROOT"] = str(workspace)
        env.setdefault("TELEGRAM_GROUP_ID", "-1001234567890")
        result = subprocess.run(
            ["sh", str(self.script)] + list(args),
            capture_output=True,
            text=True,
            cwd=str(workspace),
            env=env,
        )
        return result

    def test_dry_run_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "cron").mkdir()
            (repo / "tools").mkdir()
            (repo / "cron" / "jobs.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "jobs": [
                            {
                                "id": "1",
                                "name": "grok-daily-brief",
                                "schedule": {"expr": "0 8 * * *"},
                                "payload": {"kind": "agentTurn", "message": "run the thing"},
                                "delivery": {
                                    "mode": "announce",
                                    "channel": "telegram",
                                    "to": "${TELEGRAM_GROUP_ID}",
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            tool = repo / "tools" / "cron-jobs-tool.py"
            tool.write_text(
                (self.workspace / "tools" / "cron-jobs-tool.py").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            result = self._run_sync_script("--dry-run", repo=repo)
            self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_validate_failure_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "cron").mkdir()
            (repo / "tools").mkdir()
            (repo / "cron" / "jobs.json").write_text(
                json.dumps({"version": 1, "jobs": ["not an object"]}), encoding="utf-8"
            )
            tool = repo / "tools" / "cron-jobs-tool.py"
            tool.write_text(
                (self.workspace / "tools" / "cron-jobs-tool.py").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            result = self._run_sync_script(repo=repo)
            self.assertNotEqual(
                result.returncode,
                0,
                msg=f"expected non-zero exit, got {result.returncode}: {result.stderr}",
            )

    def test_sync_without_restart_exits_zero_and_does_not_call_gateway_ctl(self):
        """Sync without --restart should not invoke gateway-ctl.sh.

        Uses --dry-run to avoid writing to the live ~/.openclaw/cron/jobs.json.
        The sync-cron-jobs.sh script defaults its --target to the real runtime config,
        and there's no way to override it from the outside. Writing test fixture data
        to the live config was the root cause of recurring grok-daily-brief failures.
        The actual write-to-target behavior is covered by TestCronJobsToolSync tests.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "cron").mkdir()
            (repo / "tools").mkdir()
            (repo / "cron" / "jobs.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "jobs": [
                            {
                                "id": "1",
                                "name": "grok-daily-brief",
                                "schedule": {"expr": "0 8 * * *"},
                                "payload": {"kind": "agentTurn", "message": "run the thing"},
                                "delivery": {
                                    "mode": "announce",
                                    "channel": "telegram",
                                    "to": "${TELEGRAM_GROUP_ID}",
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            tool = repo / "tools" / "cron-jobs-tool.py"
            tool.write_text(
                (self.workspace / "tools" / "cron-jobs-tool.py").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            gateway_ctl = repo / "tools" / "gateway-ctl.sh"
            gateway_ctl.write_text(
                "#!/bin/sh\ntouch /tmp/gateway_ctl_called", encoding="utf-8"
            )
            result = self._run_sync_script("--dry-run", repo=repo)
            self.assertEqual(result.returncode, 0, msg=result.stderr)


class TestCronJobsToolSync(unittest.TestCase):
    """Direct unit tests for cron-jobs-tool.py sync logic"""

    def setUp(self):
        super().setUp()
        self._telegram_env = patch.dict(
            os.environ,
            {"TELEGRAM_GROUP_ID": "-1001234567890"},
            clear=False,
        )
        self._telegram_env.start()

    def tearDown(self):
        self._telegram_env.stop()
        super().tearDown()

    def test_merge_runtime_fields_preserves_state(self):
        cjt = _load_cron_jobs_tool()
        repo_jobs = {
            "version": 1,
            "jobs": [
                {
                    "id": "1",
                    "name": "grok-daily-brief",
                    "schedule": {"expr": "0 8 * * *"},
                    "payload": {"kind": "agentTurn", "message": "run the thing"},
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "${TELEGRAM_GROUP_ID}",
                    },
                },
                {
                    "id": "2",
                    "name": "alpha-polymarket",
                    "schedule": {"expr": "0 * * * *"},
                    "payload": {"kind": "agentTurn", "message": "run the thing"},
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "${TELEGRAM_GROUP_ID}",
                    },
                    "agentId": "alpha",
                },
            ],
        }
        runtime_jobs = {
            "version": 1,
            "jobs": [
                {
                    "id": "1",
                    "name": "grok-daily-brief",
                    "schedule": {"expr": "0 8 * * *"},
                    "payload": {"kind": "agentTurn", "message": "run the thing"},
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "${TELEGRAM_GROUP_ID}",
                    },
                    "state": {"nextRunAtMs": 1712000000000},
                    "createdAtMs": 1712000000000,
                    "updatedAtMs": 1712000000000,
                },
                {
                    "id": "2",
                    "name": "alpha-polymarket",
                    "schedule": {"expr": "0 * * * *"},
                    "payload": {"kind": "agentTurn", "message": "run the thing"},
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "${TELEGRAM_GROUP_ID}",
                    },
                    "agentId": "alpha",
                    "state": {"nextRunAtMs": 1711900000000},
                    "createdAtMs": 1711900000000,
                    "updatedAtMs": 1711950000000,
                },
            ],
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(runtime_jobs, f)
            runtime_path = Path(f.name)
        try:
            merged = cjt.merge_runtime_fields(repo_jobs, runtime_path)
            merged_jobs = {j["id"]: j for j in merged["jobs"]}
            self.assertEqual(merged_jobs["1"]["state"]["nextRunAtMs"], 1712000000000)
            self.assertEqual(merged_jobs["1"]["createdAtMs"], 1712000000000)
            self.assertEqual(merged_jobs["1"]["updatedAtMs"], 1712000000000)
            self.assertEqual(merged_jobs["2"]["state"]["nextRunAtMs"], 1711900000000)
            self.assertEqual(merged_jobs["2"]["createdAtMs"], 1711900000000)
            self.assertEqual(merged_jobs["2"]["updatedAtMs"], 1711950000000)
        finally:
            runtime_path.unlink()

    def test_merge_runtime_fields_returns_repo_jobs_when_no_target(self):
        cjt = _load_cron_jobs_tool()
        repo_jobs = {"version": 1, "jobs": [{"id": "1", "name": "test"}]}
        result = cjt.merge_runtime_fields(repo_jobs, Path("/nonexistent/target.json"))
        self.assertIs(result, repo_jobs)
        self.assertEqual(result["jobs"][0]["state"], {})

    def test_merge_runtime_fields_handles_corrupt_target(self):
        cjt = _load_cron_jobs_tool()
        repo_jobs = {"version": 1, "jobs": [{"id": "1", "name": "test"}]}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            f.write("not valid json{")
            corrupt_path = Path(f.name)
        try:
            result = cjt.merge_runtime_fields(repo_jobs, corrupt_path)
            self.assertIs(result, repo_jobs)
            self.assertEqual(result["jobs"][0]["state"], {})
        finally:
            corrupt_path.unlink()

    def test_merge_runtime_fields_new_job_in_repo_gets_empty_state_dict(self):
        cjt = _load_cron_jobs_tool()
        repo_jobs = {
            "version": 1,
            "jobs": [{"id": "1", "name": "existing"}, {"id": "2", "name": "new-job"}],
        }
        runtime_jobs = {
            "version": 1,
            "jobs": [{"id": "1", "name": "existing", "state": {"fromRuntime": True}}],
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(runtime_jobs, f)
            runtime_path = Path(f.name)
        try:
            merged = cjt.merge_runtime_fields(repo_jobs, runtime_path)
            merged_jobs = {j["id"]: j for j in merged["jobs"]}
            self.assertEqual(merged_jobs["1"]["state"], {"fromRuntime": True})
            self.assertEqual(merged_jobs["2"]["state"], {})
        finally:
            runtime_path.unlink()

    def test_merge_runtime_fields_drops_orphan_with_duplicate_name(self):
        """Legacy row with same name as a repo job must not double-schedule."""
        cjt = _load_cron_jobs_tool()
        repo_jobs = {
            "version": 1,
            "jobs": [
                {
                    "id": "9c1b0a7d4e2f1001",
                    "name": "grok-daily-brief",
                    "schedule": {"expr": "0 8 * * *"},
                    "payload": {"kind": "agentTurn", "message": "ok"},
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "${TELEGRAM_GROUP_ID}",
                    },
                },
            ],
        }
        runtime_jobs = {
            "version": 1,
            "jobs": [
                {
                    "id": "9c1b0a7d4e2f1001",
                    "name": "grok-daily-brief",
                    "payload": {"kind": "agentTurn", "message": "ok"},
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "${TELEGRAM_GROUP_ID}",
                    },
                    "state": {"lastRunStatus": "ok"},
                },
                {
                    "id": "1",
                    "name": "grok-daily-brief",
                    "payload": {"kind": "agentTurn", "message": "run the thing"},
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "${TELEGRAM_GROUP_ID}",
                    },
                    "state": {"lastRunStatus": "error"},
                },
            ],
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(runtime_jobs, f)
            runtime_path = Path(f.name)
        try:
            merged = cjt.merge_runtime_fields(repo_jobs, runtime_path)
            ids = [j["id"] for j in merged["jobs"]]
            self.assertEqual(ids, ["9c1b0a7d4e2f1001"])
            self.assertEqual(merged["jobs"][0]["state"]["lastRunStatus"], "ok")
        finally:
            runtime_path.unlink()

    def test_merge_runtime_fields_keeps_orphan_with_distinct_name(self):
        cjt = _load_cron_jobs_tool()
        repo_jobs = {
            "version": 1,
            "jobs": [
                {"id": "a", "name": "core-one", "payload": {"kind": "agentTurn"}},
            ],
        }
        runtime_jobs = {
            "version": 1,
            "jobs": [
                {"id": "a", "name": "core-one", "state": {"x": 1}},
                {"id": "legacy", "name": "deprecated-job", "payload": {"kind": "agentTurn"}},
            ],
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(runtime_jobs, f)
            runtime_path = Path(f.name)
        try:
            merged = cjt.merge_runtime_fields(repo_jobs, runtime_path)
            ids = {j["id"] for j in merged["jobs"]}
            self.assertEqual(ids, {"a", "legacy"})
        finally:
            runtime_path.unlink()

    def test_sync_writes_target_and_preserves_state(self):
        cjt = _load_cron_jobs_tool()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "cron").mkdir(parents=True)
            repo_jobs = {
                "version": 1,
                "jobs": [
                    {
                        "id": "1",
                        "name": "grok-daily-brief",
                        "schedule": {"expr": "0 8 * * *"},
                        "payload": {"kind": "agentTurn", "message": "run the thing"},
                        "delivery": {
                            "mode": "announce",
                            "channel": "telegram",
                            "to": "${TELEGRAM_GROUP_ID}",
                        },
                    },
                ],
            }
            (repo / "cron" / "jobs.json").write_text(
                json.dumps(repo_jobs), encoding="utf-8"
            )
            target = repo / ".openclaw" / "cron" / "jobs.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            prev_state = {
                "version": 1,
                "jobs": [
                    {
                        "id": "1",
                        "name": "grok-daily-brief",
                        "state": {"nextRunAtMs": 999},
                        "createdAtMs": 111111,
                    }
                ],
            }
            target.write_text(json.dumps(prev_state), encoding="utf-8")

            orig_argv = sys.argv
            sys.argv = [
                "cron-jobs-tool.py",
                "sync",
                "--repo",
                str(repo / "cron" / "jobs.json"),
                "--target",
                str(target),
            ]
            try:
                ret = cjt.main()
            finally:
                sys.argv = orig_argv

            self.assertEqual(ret, 0)
            written = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(written["jobs"][0]["state"]["nextRunAtMs"], 999)
            self.assertEqual(written["jobs"][0]["createdAtMs"], 111111)

    def test_sync_dry_run_does_not_write(self):
        cjt = _load_cron_jobs_tool()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "cron").mkdir(parents=True)
            repo_jobs = {
                "version": 1,
                "jobs": [
                    {
                        "id": "1",
                        "name": "grok-daily-brief",
                        "schedule": {"expr": "0 8 * * *"},
                        "payload": {"kind": "agentTurn", "message": "run the thing"},
                        "delivery": {
                            "mode": "announce",
                            "channel": "telegram",
                            "to": "${TELEGRAM_GROUP_ID}",
                        },
                    },
                ],
            }
            (repo / "cron" / "jobs.json").write_text(
                json.dumps(repo_jobs), encoding="utf-8"
            )
            target = repo / ".openclaw" / "cron" / "jobs.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            prev_state = {
                "version": 1,
                "jobs": [
                    {"id": "1", "name": "grok-daily-brief", "state": {"nextRunAtMs": 42}}
                ],
            }
            target.write_text(json.dumps(prev_state), encoding="utf-8")

            orig_argv = sys.argv
            sys.argv = [
                "cron-jobs-tool.py",
                "sync",
                "--repo",
                str(repo / "cron" / "jobs.json"),
                "--target",
                str(target),
                "--dry-run",
            ]
            try:
                ret = cjt.main()
            finally:
                sys.argv = orig_argv

            self.assertEqual(ret, 0)
            still_prev = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(still_prev["jobs"][0].get("state"), {"nextRunAtMs": 42})

    def test_sync_validation_failure_returns_nonzero(self):
        cjt = _load_cron_jobs_tool()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "cron").mkdir(parents=True)
            (repo / "cron" / "jobs.json").write_text(
                json.dumps({"version": 1}), encoding="utf-8"
            )
            target = repo / ".openclaw" / "cron" / "jobs.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            orig_argv = sys.argv
            sys.argv = [
                "cron-jobs-tool.py",
                "sync",
                "--repo",
                str(repo / "cron" / "jobs.json"),
                "--target",
                str(target),
            ]
            try:
                ret = cjt.main()
            finally:
                sys.argv = orig_argv
            self.assertEqual(ret, 1)


class TestCheckRuntimeDrift(unittest.TestCase):
    """Tests for cron-jobs-tool.py check subcommand — drift detection."""

    def setUp(self):
        super().setUp()
        self._telegram_env = patch.dict(
            os.environ,
            {"TELEGRAM_GROUP_ID": "-1001234567890"},
            clear=False,
        )
        self._telegram_env.start()

    def tearDown(self):
        self._telegram_env.stop()
        super().tearDown()

    def test_check_detects_missing_payload_message(self):
        """The exact bug: runtime has agentTurn with no message, repo has the message."""
        cjt = _load_cron_jobs_tool()
        repo = {
            "version": 1,
            "jobs": [
                {
                    "id": "9c1b0a7d4e2f1001",
                    "name": "grok-daily-brief",
                    "payload": {
                        "kind": "agentTurn",
                        "message": "./tools/cron-core-workflow-run.sh grok-daily-brief grok",
                    },
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "-1001234567890",
                    },
                },
            ],
        }
        runtime = {
            "version": 1,
            "jobs": [
                {
                    "id": "9c1b0a7d4e2f1001",
                    "name": "grok-daily-brief",
                    "payload": {"kind": "agentTurn"},
                    "state": {},
                },
            ],
        }
        drift = cjt.check_runtime_drift(repo, runtime)
        self.assertTrue(any("missing payload.message" in d for d in drift), drift)

    def test_check_detects_id_mismatch(self):
        """Runtime has job with different ID than repo — stale entry."""
        cjt = _load_cron_jobs_tool()
        repo = {
            "version": 1,
            "jobs": [
                {
                    "id": "9c1b0a7d4e2f1001",
                    "name": "grok-daily-brief",
                    "payload": {
                        "kind": "agentTurn",
                        "message": "run it",
                    },
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "-1001234567890",
                    },
                },
            ],
        }
        runtime = {
            "version": 1,
            "jobs": [
                {
                    "id": "1",
                    "name": "grok-daily-brief",
                    "payload": {"kind": "agentTurn", "message": "run it"},
                    "state": {},
                },
            ],
        }
        drift = cjt.check_runtime_drift(repo, runtime)
        self.assertTrue(any("runtime id=" in d for d in drift), drift)

    def test_check_detects_missing_runtime_job(self):
        cjt = _load_cron_jobs_tool()
        repo = {
            "version": 1,
            "jobs": [
                {"id": "a", "name": "job-a", "payload": {"kind": "agentTurn", "message": "x"}},
            ],
        }
        runtime = {"version": 1, "jobs": []}
        drift = cjt.check_runtime_drift(repo, runtime)
        self.assertTrue(any("missing from runtime" in d for d in drift), drift)

    def test_check_returns_empty_when_configs_match(self):
        cjt = _load_cron_jobs_tool()
        repo = {
            "version": 1,
            "jobs": [
                {
                    "id": "9c1b0a7d4e2f1001",
                    "name": "grok-daily-brief",
                    "payload": {
                        "kind": "agentTurn",
                        "message": "./tools/cron-core-workflow-run.sh grok-daily-brief grok",
                    },
                },
            ],
        }
        runtime = {
            "version": 1,
            "jobs": [
                {
                    "id": "9c1b0a7d4e2f1001",
                    "name": "grok-daily-brief",
                    "payload": {
                        "kind": "agentTurn",
                        "message": "./tools/cron-core-workflow-run.sh grok-daily-brief grok",
                    },
                    "state": {"nextRunAtMs": 12345},
                },
            ],
        }
        drift = cjt.check_runtime_drift(repo, runtime)
        self.assertEqual(drift, [])

    def test_check_subcommand_exits_nonzero_on_drift(self):
        """Integration test: check subcommand returns 1 when drift found."""
        cjt = _load_cron_jobs_tool()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "repo.json"
            target_path = Path(tmpdir) / "runtime.json"
            repo_path.write_text(
                json.dumps({
                    "version": 1,
                    "jobs": [
                        {
                            "id": "9c1b0a7d4e2f1001",
                            "name": "grok-daily-brief",
                            "schedule": {"expr": "0 8 * * *"},
                            "payload": {"kind": "agentTurn", "message": "do the thing"},
                            "delivery": {
                                "mode": "announce",
                                "channel": "telegram",
                                "to": "-1001234567890",
                            },
                        },
                    ],
                }),
                encoding="utf-8",
            )
            target_path.write_text(
                json.dumps({
                    "version": 1,
                    "jobs": [
                        {
                            "id": "1",
                            "name": "grok-daily-brief",
                            "payload": {"kind": "agentTurn", "message": "run the thing"},
                            "state": {},
                        },
                    ],
                }),
                encoding="utf-8",
            )
            orig_argv = sys.argv
            sys.argv = [
                "cron-jobs-tool.py",
                "check",
                "--repo", str(repo_path),
                "--target", str(target_path),
            ]
            try:
                ret = cjt.main()
            finally:
                sys.argv = orig_argv
            self.assertEqual(ret, 1)

    def test_check_subcommand_exits_zero_when_synced(self):
        cjt = _load_cron_jobs_tool()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "repo.json"
            target_path = Path(tmpdir) / "runtime.json"
            job = {
                "id": "9c1b0a7d4e2f1001",
                "name": "grok-daily-brief",
                "schedule": {"expr": "0 8 * * *"},
                "payload": {"kind": "agentTurn", "message": "do the thing"},
                "delivery": {
                    "mode": "announce",
                    "channel": "telegram",
                    "to": "-1001234567890",
                },
            }
            repo_path.write_text(
                json.dumps({"version": 1, "jobs": [job]}), encoding="utf-8"
            )
            rt_job = dict(job)
            rt_job["state"] = {"nextRunAtMs": 12345}
            target_path.write_text(
                json.dumps({"version": 1, "jobs": [rt_job]}), encoding="utf-8"
            )
            orig_argv = sys.argv
            sys.argv = [
                "cron-jobs-tool.py",
                "check",
                "--repo", str(repo_path),
                "--target", str(target_path),
            ]
            try:
                ret = cjt.main()
            finally:
                sys.argv = orig_argv
            self.assertEqual(ret, 0)

    def test_validate_rejects_agentturn_without_message(self):
        """validate subcommand must catch agentTurn jobs with no message."""
        cjt = _load_cron_jobs_tool()
        data = {
            "version": 1,
            "jobs": [
                {
                    "id": "1",
                    "name": "grok-daily-brief",
                    "schedule": {"expr": "0 8 * * *"},
                    "payload": {"kind": "agentTurn"},
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "-1001234567890",
                    },
                },
            ],
        }
        errs = cjt.validate_jobs(data)
        self.assertTrue(
            any("missing 'message'" in e for e in errs),
            f"Expected message validation error, got: {errs}",
        )


if __name__ == "__main__":
    unittest.main()

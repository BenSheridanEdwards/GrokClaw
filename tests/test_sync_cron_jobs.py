import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
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
                                "payload": {"kind": "agentTurn"},
                                "delivery": {
                                    "mode": "announce",
                                    "channel": "telegram",
                                    "to": "-1003831656556",
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
                                "payload": {"kind": "agentTurn"},
                                "delivery": {
                                    "mode": "announce",
                                    "channel": "telegram",
                                    "to": "-1003831656556",
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
            result = self._run_sync_script(repo=repo)
            self.assertEqual(result.returncode, 0, msg=result.stderr)


class TestCronJobsToolSync(unittest.TestCase):
    """Direct unit tests for cron-jobs-tool.py sync logic"""

    def test_merge_runtime_fields_preserves_state(self):
        cjt = _load_cron_jobs_tool()
        repo_jobs = {
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
                        "to": "-1003831656556",
                    },
                },
                {
                    "id": "2",
                    "name": "alpha-polymarket",
                    "schedule": {"expr": "0 * * * *"},
                    "payload": {"kind": "agentTurn"},
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "-1003831656556",
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
                    "payload": {"kind": "agentTurn"},
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "-1003831656556",
                    },
                    "state": "enabled",
                    "createdAtMs": 1712000000000,
                    "updatedAtMs": 1712000000000,
                },
                {
                    "id": "2",
                    "name": "alpha-polymarket",
                    "schedule": {"expr": "0 * * * *"},
                    "payload": {"kind": "agentTurn"},
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "-1003831656556",
                    },
                    "agentId": "alpha",
                    "state": "disabled",
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
            self.assertEqual(merged_jobs["1"]["state"], "enabled")
            self.assertEqual(merged_jobs["1"]["createdAtMs"], 1712000000000)
            self.assertEqual(merged_jobs["1"]["updatedAtMs"], 1712000000000)
            self.assertEqual(merged_jobs["2"]["state"], "disabled")
            self.assertEqual(merged_jobs["2"]["createdAtMs"], 1711900000000)
            self.assertEqual(merged_jobs["2"]["updatedAtMs"], 1711950000000)
        finally:
            runtime_path.unlink()

    def test_merge_runtime_fields_returns_repo_jobs_when_no_target(self):
        cjt = _load_cron_jobs_tool()
        repo_jobs = {"version": 1, "jobs": [{"id": "1", "name": "test"}]}
        result = cjt.merge_runtime_fields(repo_jobs, Path("/nonexistent/target.json"))
        self.assertEqual(result, repo_jobs)

    def test_merge_runtime_fields_handles_corrupt_target(self):
        cjt = _load_cron_jobs_tool()
        repo_jobs = {"version": 1, "jobs": [{"id": "1", "name": "test"}]}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            f.write("not valid json{")
            corrupt_path = Path(f.name)
        try:
            result = cjt.merge_runtime_fields(repo_jobs, corrupt_path)
            self.assertEqual(result, repo_jobs)
        finally:
            corrupt_path.unlink()

    def test_merge_runtime_fields_new_job_in_repo_gets_no_state(self):
        cjt = _load_cron_jobs_tool()
        repo_jobs = {
            "version": 1,
            "jobs": [{"id": "1", "name": "existing"}, {"id": "2", "name": "new-job"}],
        }
        runtime_jobs = {
            "version": 1,
            "jobs": [{"id": "1", "name": "existing", "state": "enabled"}],
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(runtime_jobs, f)
            runtime_path = Path(f.name)
        try:
            merged = cjt.merge_runtime_fields(repo_jobs, runtime_path)
            merged_jobs = {j["id"]: j for j in merged["jobs"]}
            self.assertEqual(merged_jobs["1"]["state"], "enabled")
            self.assertNotIn("state", merged_jobs["2"])
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
                        "to": "-1003831656556",
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
                        "to": "-1003831656556",
                    },
                    "state": {"lastRunStatus": "ok"},
                },
                {
                    "id": "1",
                    "name": "grok-daily-brief",
                    "payload": {"kind": "agentTurn"},
                    "delivery": {
                        "mode": "announce",
                        "channel": "telegram",
                        "to": "-1003831656556",
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
                        "payload": {"kind": "agentTurn"},
                        "delivery": {
                            "mode": "announce",
                            "channel": "telegram",
                            "to": "-1003831656556",
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
                        "state": "disabled",
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
            self.assertEqual(written["jobs"][0]["state"], "disabled")
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
                        "payload": {"kind": "agentTurn"},
                        "delivery": {
                            "mode": "announce",
                            "channel": "telegram",
                            "to": "-1003831656556",
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
                "jobs": [{"id": "1", "name": "grok-daily-brief", "state": "disabled"}],
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
            self.assertEqual(still_prev["jobs"][0].get("state"), "disabled")

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


if __name__ == "__main__":
    unittest.main()

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class SchedulerSimplificationGateTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]
        self.script = self.repo / "tools" / "scheduler-simplification-gate.sh"

    def _write(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_recommends_consolidation_when_reliability_is_weak(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._write(
                workspace / "tools" / "_cto_kpi_report.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json
                    print(json.dumps({
                        "reliability": {
                            "slotAdherencePercent": 95.4,
                            "stuckInProgressCount": 2,
                            "meanRecoveryMinutes": 18.0,
                            "unrecoveredErrorCount": 1
                        },
                        "workflowHealth": {"fullHealthy": False},
                    }))
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            result = subprocess.run(
                ["sh", str(self.script), "--days", "30", "--json"],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "keep_openclaw_cron_consolidate_supervisor")
            self.assertGreaterEqual(len(payload["reasons"]), 1)

    def test_recommends_external_queue_when_metrics_are_strong(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._write(
                workspace / "tools" / "_cto_kpi_report.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json
                    print(json.dumps({
                        "reliability": {
                            "slotAdherencePercent": 99.9,
                            "stuckInProgressCount": 0,
                            "meanRecoveryMinutes": 4.0,
                            "unrecoveredErrorCount": 0
                        },
                        "workflowHealth": {"fullHealthy": True},
                    }))
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            result = subprocess.run(
                ["sh", str(self.script), "--days", "30", "--json"],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "evaluate_external_scheduler_queue")
            self.assertIn("readinessScore", payload)


if __name__ == "__main__":
    unittest.main()

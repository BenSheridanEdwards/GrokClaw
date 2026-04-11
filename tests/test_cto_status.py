import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class CtoStatusTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]
        self.script = self.repo / "tools" / "cto-status.sh"

    def _write(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_status_merges_kpis_and_latest_run_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._write(
                workspace / "tools" / "_cto_kpi_report.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json
                    print(json.dumps({
                        "window": {"start": "2026-04-01T00:00:00Z", "end": "2026-04-01T23:59:59Z", "days": 1},
                        "reliability": {"slotAdherencePercent": 95.0, "stuckInProgressCount": 0},
                        "economics": {"runsWithUsagePercent": 80.0, "runsWithCostPercent": 60.0},
                        "workflowHealth": {"quickHealthy": True, "fullHealthy": False, "fullFailureCount": 1},
                    }))
                    """
                ),
            )

            runs = workspace / "data" / "cron-runs"
            runs.mkdir(parents=True, exist_ok=True)
            (runs / "2026-04-01.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "job": "alpha-polymarket",
                                "agent": "alpha",
                                "ts": "2026-04-01T10:00:00Z",
                                "status": "ok",
                                "summary": "trade placed",
                                "runId": "run-1",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                [
                    "sh",
                    str(self.script),
                    "--offline",
                    "--json",
                    "--date",
                    "2026-04-01",
                    "--days",
                    "1",
                ],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["kpis"]["reliability"]["slotAdherencePercent"], 95.0)
            self.assertEqual(payload["serviceHealth"]["gateway"], "unknown")
            self.assertEqual(payload["serviceHealth"]["paperclip"], "unknown")
            self.assertEqual(payload["latestRuns"][0]["job"], "alpha-polymarket")
            self.assertEqual(payload["latestRuns"][0]["runId"], "run-1")


if __name__ == "__main__":
    unittest.main()

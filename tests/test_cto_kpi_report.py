import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class CtoKpiReportTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]
        self.script = self.repo / "tools" / "cto-kpi-report.sh"

    def _write(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    def test_generates_reliability_and_economics_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            cron_dir = workspace / "data" / "cron-runs"
            cron_dir.mkdir(parents=True, exist_ok=True)
            cron_records = [
                {
                    "job": "alpha-polymarket",
                    "agent": "alpha",
                    "ts": "2026-04-01T09:00:01Z",
                    "status": "error",
                    "summary": "provider timeout",
                },
                {
                    "job": "alpha-polymarket",
                    "agent": "alpha",
                    "ts": "2026-04-01T10:05:00Z",
                    "status": "ok",
                    "summary": "trade placed",
                },
                {
                    "job": "grok-openclaw-research",
                    "agent": "grok",
                    "ts": "2026-04-01T07:05:00Z",
                    "status": "ok",
                    "summary": "research saved",
                },
                {
                    "job": "grok-daily-brief",
                    "agent": "grok",
                    "ts": "2026-04-01T08:04:00Z",
                    "status": "ok",
                    "summary": "brief posted",
                },
            ]
            self._write(
                cron_dir / "2026-04-01.jsonl",
                "\n".join(json.dumps(entry) for entry in cron_records) + "\n",
            )

            # Stub workflow health script to keep test deterministic.
            self._write(
                workspace / "tools" / "_workflow_health.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json
                    import sys

                    cmd = sys.argv[1]
                    if cmd == "audit-quick":
                        print(json.dumps({"healthy": True, "failures": []}))
                    elif cmd == "audit":
                        print(json.dumps({"healthy": False, "failures": [{"workflow": "alpha-polymarket", "kind": "error_run"}]}))
                    else:
                        print(json.dumps({"healthy": True, "failures": []}))
                    """
                ),
            )
            (workspace / "tools" / "_workflow_health.py").chmod(0o755)

            runs_payload = [
                {
                    "id": "run-1",
                    "agentId": "agent-a",
                    "createdAt": "2026-04-01T07:00:00Z",
                    "usageJson": {"inputTokens": 100, "outputTokens": 50, "costUsd": 0.12},
                },
                {
                    "id": "run-2",
                    "agentId": "agent-a",
                    "createdAt": "2026-04-01T08:00:00Z",
                    "usageJson": {"input_tokens": 70, "output_tokens": 20, "cost_usd": 0.05},
                },
                {
                    "id": "run-3",
                    "agentId": "agent-b",
                    "createdAt": "2026-04-01T09:00:00Z",
                    "usageJson": {"rawInputTokens": 40, "rawOutputTokens": 15},
                },
                {
                    "id": "run-4",
                    "agentId": "agent-b",
                    "createdAt": "2026-04-01T10:00:00Z",
                    "usageJson": None,
                },
            ]
            runs_file = workspace / "paperclip-runs.json"
            self._write(runs_file, json.dumps(runs_payload))

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            result = subprocess.run(
                [
                    "sh",
                    str(self.script),
                    "--date",
                    "2026-04-01",
                    "--days",
                    "1",
                    "--json",
                    "--paperclip-runs-file",
                    str(runs_file),
                ],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)

            self.assertIn("reliability", payload)
            self.assertIn("economics", payload)
            self.assertEqual(payload["workflowHealth"]["quickHealthy"], True)
            self.assertEqual(payload["workflowHealth"]["fullHealthy"], False)

            reliability = payload["reliability"]
            self.assertEqual(reliability["statusCounts"]["error"], 1)
            self.assertEqual(reliability["statusCounts"]["ok"], 3)
            self.assertGreaterEqual(reliability["meanRecoveryMinutes"], 60.0)
            self.assertEqual(reliability["unrecoveredErrorCount"], 0)

            economics = payload["economics"]
            self.assertEqual(economics["totalRuns"], 4)
            self.assertEqual(economics["runsWithUsage"], 3)
            self.assertEqual(economics["runsWithCost"], 2)
            self.assertEqual(economics["totalInputTokens"], 210)
            self.assertEqual(economics["totalOutputTokens"], 85)
            self.assertAlmostEqual(economics["totalCostUsd"], 0.17, places=6)


if __name__ == "__main__":
    unittest.main()

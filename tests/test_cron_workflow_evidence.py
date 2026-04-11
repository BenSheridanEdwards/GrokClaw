import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class CronWorkflowEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]
        self.script = self.repo / "tools" / "cron-workflow-evidence.sh"

    def _write_stub(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def _seed_cron_run(self, workspace: Path, job: str, agent: str, run_id: str, started_ts: str, terminal_ts: str) -> None:
        run_dir = workspace / "data" / "cron-runs"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "2026-04-09.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "job": job,
                            "agent": agent,
                            "ts": started_ts,
                            "status": "started",
                            "summary": "run started",
                            "runId": run_id,
                        }
                    ),
                    json.dumps(
                        {
                            "job": job,
                            "agent": agent,
                            "ts": terminal_ts,
                            "status": "ok",
                            "summary": "orchestrator: agent completed successfully",
                            "runId": run_id,
                        }
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def test_alpha_enforcer_backfills_research_report_and_telegram(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            run_id = "run-alpha-1"
            self._seed_cron_run(
                workspace,
                job="alpha-polymarket",
                agent="alpha",
                run_id=run_id,
                started_ts="2026-04-09T07:51:59Z",
                terminal_ts="2026-04-09T07:52:10Z",
            )

            audit_log = workspace / "data" / "audit-log" / "2026-04-09.jsonl"
            self._write_stub(
                workspace / "tools" / "telegram-post.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    mkdir -p "{workspace / 'data' / 'audit-log'}"
                    printf '{{"ts":"2026-04-09T07:52:11Z","kind":"telegram_post","topic":"%s","message":"%s"}}\\n' "$1" "$2" >> "{audit_log}"
                    """
                ),
            )
            self._write_stub(
                workspace / "tools" / "agent-report.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    mkdir -p "{workspace / 'data' / 'agent-reports'}"
                    cat > "{workspace / 'data' / 'agent-reports' / '2026-04-09.json'}" <<'JSON'
                    {{"reports":[{{"agent":"alpha","job":"alpha-polymarket","timestamp":"2026-04-09T07:52:12Z","summary":"fallback"}}]}}
                    JSON
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["CRON_RUN_ID"] = run_id
            result = subprocess.run(
                ["sh", str(self.script), "alpha-polymarket", "alpha"],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            expected_research = workspace / "data" / "alpha" / "research" / "2026-04-09-07.md"
            self.assertTrue(expected_research.exists(), "enforcer should create expected alpha research file")
            self.assertTrue((workspace / "data" / "agent-reports" / "2026-04-09.json").exists(), "enforcer should create agent report evidence")
            self.assertTrue(audit_log.exists(), "enforcer should post fallback Telegram line")
            self.assertIn("Alpha · Hourly · HOLD", audit_log.read_text(encoding="utf-8"))



if __name__ == "__main__":
    unittest.main()

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class CronWorkflowLayersTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]
        self.check_script = self.repo / "tools" / "cron-workflow-check.sh"
        self.report_script = self.repo / "tools" / "cron-workflow-report.sh"

    def _write_stub(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_check_layer_writes_result_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            self._write_stub(
                workspace / "tools" / "_workflow_health.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json
                    print(json.dumps({"healthy": False, "failureHash": "abc123", "failures": [{"workflow": "alpha-polymarket"}]}))
                    """
                ),
            )
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["CRON_RUN_ID"] = "run-123"

            result = subprocess.run(
                ["sh", str(self.check_script), "alpha-polymarket"],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output_path = Path(result.stdout.strip())
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["failureHash"], "abc123")

    def test_report_layer_passes_payload_to_handler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            check_dir = workspace / "data" / "workflow-health" / "checks"
            check_dir.mkdir(parents=True, exist_ok=True)
            payload_path = check_dir / "alpha-polymarket-latest.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "healthy": False,
                        "failureHash": "err123",
                        "alertMessage": "Workflow unhealthy",
                        "failures": [{"workflow": "alpha-polymarket"}],
                    }
                ),
                encoding="utf-8",
            )

            handler_log = workspace / "handler.log"
            self._write_stub(
                workspace / "tools" / "_workflow_health_handle.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import sys
                    with open("{handler_log}", "a", encoding="utf-8") as handle:
                        handle.write(sys.stdin.read())
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["CRON_RUN_ID"] = "run-987"
            result = subprocess.run(
                ["sh", str(self.report_script), "alpha-polymarket"],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(handler_log.exists())
            self.assertIn('"failureHash": "err123"', handler_log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class CronWorkflowLayersE2ETests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]
        self.wrapper = self.repo / "tools" / "cron-core-workflow-run.sh"

    def _write_stub(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_orchestrator_runs_operational_check_and_reporting_layers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            tools = tmp / "tools"
            tools.mkdir(parents=True, exist_ok=True)
            bin_dir = tmp / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)

            # lifecycle + API stubs
            self._write_stub(
                tools / "cron-paperclip-lifecycle.sh",
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    if [ "$1" = "start" ]; then
                      echo "issue-123"
                      exit 0
                    fi
                    exit 0
                    """
                ),
            )
            self._write_stub(
                tools / "paperclip-api.sh",
                "#!/bin/sh\nset -eu\nexit 0\n",
            )
            self._write_stub(
                tools / "telegram-post.sh",
                "#!/bin/sh\nset -eu\nexit 0\n",
            )

            # copy real layered scripts from repo
            for script_name in [
                "cron-run-record.sh",
                "cron-workflow-check.sh",
                "cron-workflow-report.sh",
            ]:
                src = self.repo / "tools" / script_name
                dst = tools / script_name
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                dst.chmod(0o755)

            # workflow-health checker + handler stubs
            self._write_stub(
                tools / "_workflow_health.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json
                    print(json.dumps({"healthy": False, "failureHash": "e2e123", "alertMessage": "e2e unhealthy", "failures": [{"workflow": "grok-daily-brief"}]}))
                    """
                ),
            )
            handler_log = tmp / "handler.log"
            self._write_stub(
                tools / "_workflow_health_handle.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import sys
                    with open("{handler_log}", "a", encoding="utf-8") as handle:
                        handle.write(sys.stdin.read())
                    """
                ),
            )

            # prompt + fake openclaw
            prompts = tmp / "docs" / "prompts"
            prompts.mkdir(parents=True, exist_ok=True)
            (prompts / "cron-work-grok-daily-brief.md").write_text("work body\n", encoding="utf-8")
            self._write_stub(
                bin_dir / "openclaw",
                "#!/bin/sh\nset -eu\necho ok\nexit 0\n",
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(tmp)
            env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
            env["OPENCLAW_BIN"] = str(bin_dir / "openclaw")

            result = subprocess.run(
                ["bash", str(self.wrapper), "grok-daily-brief", "grok"],
                cwd=str(tmp),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            # operational evidence
            day_file = next((tmp / "data" / "cron-runs").glob("*.jsonl"))
            lines = [json.loads(line) for line in day_file.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(lines[0]["status"], "started")
            self.assertEqual(lines[1]["status"], "ok")

            # checking artifacts
            check_latest = tmp / "data" / "workflow-health" / "checks" / "grok-daily-brief-latest.json"
            self.assertTrue(check_latest.exists(), "checking layer should emit latest check artifact")

            # reporting artifacts + handler ingestion
            report_dir = tmp / "data" / "workflow-health" / "reports"
            report_files = list(report_dir.glob("grok-daily-brief-*.json"))
            self.assertTrue(report_files, "reporting layer should persist report artifact")
            self.assertTrue(handler_log.exists(), "reporting layer should invoke health handler")
            self.assertIn('"failureHash": "e2e123"', handler_log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class CronCoreWorkflowRunTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]
        self.wrapper = self.repo / "tools" / "cron-core-workflow-run.sh"

    def _write_stub(self, path: Path, body: str) -> None:
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def _seed_temp_workspace(self, openclaw_exit: int) -> tuple[Path, Path]:
        tmp = Path(tempfile.mkdtemp())
        tools = tmp / "tools"
        tools.mkdir(parents=True)
        bin_dir = tmp / "bin"
        bin_dir.mkdir(parents=True)
        lifecycle_log = tmp / "lifecycle.log"

        self._write_stub(
            tools / "cron-paperclip-lifecycle.sh",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                set -eu
                if [ "$1" = "start" ]; then
                  printf 'start %s\\n' "$*" >>"{lifecycle_log}"
                  echo "test-issue-uuid"
                  exit 0
                fi
                printf '%s\\n' "$*" >>"{lifecycle_log}"
                """
            ),
        )
        telegram_log = tmp / "telegram.log"
        self._write_stub(
            tools / "telegram-post.sh",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                set -eu
                printf '%s\\n' "$*" >> "{telegram_log}"
                """
            ),
        )
        self._write_stub(
            tools / "paperclip-api.sh",
            textwrap.dedent(
                """\
                #!/bin/sh
                set -eu
                exit 0
                """
            ),
        )
        audit_log = tmp / "audit.log"
        handler_log = tmp / "handler.log"
        self._write_stub(
            tools / "_workflow_health.py",
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import json, sys
                out = {{"healthy": True, "failures": [], "failureHash": "x", "alertMessage": "ok", "draft": None}}
                print(json.dumps(out))
                sys.exit(0)
                """
            ),
        )
        self._write_stub(
            tools / "_workflow_health_handle.py",
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                open("{handler_log}", "a").write("handled\\n")
                """
            ),
        )

        cr_src = self.repo / "tools" / "cron-run-record.sh"
        (tools / "cron-run-record.sh").write_text(cr_src.read_text(encoding="utf-8"), encoding="utf-8")
        (tools / "cron-run-record.sh").chmod(0o755)

        prompts = tmp / "docs" / "prompts"
        prompts.mkdir(parents=True)
        (prompts / "cron-work-grok-daily-brief.md").write_text(
            "Work-only body.\nDo not call cron-run-record.\n", encoding="utf-8"
        )

        self._write_stub(
            bin_dir / "openclaw",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                exit {openclaw_exit}
                """
            ),
        )

        return tmp, lifecycle_log

    def test_orchestrator_records_ok_when_openclaw_succeeds(self):
        tmp, lifecycle_log = self._seed_temp_workspace(0)
        try:
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(tmp)
            env["PATH"] = f"{tmp / 'bin'}:{env.get('PATH', '')}"
            env["OPENCLAW_BIN"] = str(tmp / "bin" / "openclaw")
            result = subprocess.run(
                ["bash", str(self.wrapper), "grok-daily-brief", "grok"],
                cwd=str(tmp),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            runs = tmp / "data" / "cron-runs"
            day_files = list(runs.glob("*.jsonl"))
            self.assertEqual(len(day_files), 1)
            lines = [
                json.loads(line)
                for line in day_files[0].read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(lines[0]["status"], "started")
            self.assertEqual(lines[1]["status"], "ok")
            self.assertIn("orchestrator", lines[1]["summary"])

            log_text = lifecycle_log.read_text(encoding="utf-8")
            self.assertIn("start grok-daily-brief grok", log_text)
            self.assertIn("finish test-issue-uuid ok", log_text)
            self.assertFalse((tmp / ".openclaw" / "grok-daily-brief.issue").exists())
        finally:
            subprocess.run(["rm", "-rf", str(tmp)], check=False)

    def test_orchestrator_records_error_when_openclaw_fails(self):
        tmp, lifecycle_log = self._seed_temp_workspace(7)
        try:
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(tmp)
            env["PATH"] = f"{tmp / 'bin'}:{env.get('PATH', '')}"
            env["OPENCLAW_BIN"] = str(tmp / "bin" / "openclaw")
            result = subprocess.run(
                ["bash", str(self.wrapper), "grok-daily-brief", "grok"],
                cwd=str(tmp),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 7, msg=result.stderr or result.stdout)

            runs = tmp / "data" / "cron-runs"
            day_file = next(runs.glob("*.jsonl"))
            lines = [
                json.loads(line)
                for line in day_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(lines[0]["status"], "started")
            self.assertEqual(lines[1]["status"], "error")
            self.assertIn("orchestrator", lines[1]["summary"])

            log_text = lifecycle_log.read_text(encoding="utf-8")
            self.assertIn("finish test-issue-uuid error", log_text)
        finally:
            subprocess.run(["rm", "-rf", str(tmp)], check=False)

    def test_orchestrator_records_error_on_simulated_timeout_exit(self):
        """Stub non-zero exit (e.g. 124) as timeout/tool kill proxy; terminal record must still run."""
        tmp, lifecycle_log = self._seed_temp_workspace(124)
        try:
            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(tmp)
            env["PATH"] = f"{tmp / 'bin'}:{env.get('PATH', '')}"
            env["OPENCLAW_BIN"] = str(tmp / "bin" / "openclaw")
            env["OPENCLAW_AGENT_TIMEOUT_SECONDS"] = "1"
            result = subprocess.run(
                ["bash", str(self.wrapper), "grok-daily-brief", "grok"],
                cwd=str(tmp),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 124, msg=result.stderr or result.stdout)

            runs = tmp / "data" / "cron-runs"
            day_file = next(runs.glob("*.jsonl"))
            lines = [
                json.loads(line)
                for line in day_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(lines[0]["status"], "started")
            self.assertEqual(lines[1]["status"], "error")
            self.assertIn("124", lines[1]["summary"])

            log_text = lifecycle_log.read_text(encoding="utf-8")
            self.assertIn("finish test-issue-uuid error", log_text)
        finally:
            subprocess.run(["rm", "-rf", str(tmp)], check=False)


if __name__ == "__main__":
    unittest.main()

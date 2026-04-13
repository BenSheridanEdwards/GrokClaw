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

        self._write_stub(
            tools / "alpha-polymarket-deterministic.sh",
            textwrap.dedent(
                """\
                #!/bin/sh
                set -eu
                echo '{"decisionAction":"skip","selectionSource":"deterministic-test"}'
                """
            ),
        )
        prompts = tmp / "docs" / "prompts"
        prompts.mkdir(parents=True)
        (prompts / "cron-work-grok-daily-brief.md").write_text(
            "Work-only body.\nDo not call cron-run-record.\n", encoding="utf-8"
        )
        (prompts / "cron-work-alpha-polymarket.md").write_text(
            "Work-only alpha prompt body.\n", encoding="utf-8"
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
            self.assertTrue(lines[0].get("runId"))
            self.assertEqual(lines[0].get("runId"), lines[1].get("runId"))

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
            day_file = next(runs.glob("2*-*-*.jsonl"))
            lines = [
                json.loads(line)
                for line in day_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(lines[0]["status"], "started")
            self.assertEqual(lines[1]["status"], "error")
            self.assertIn("orchestrator", lines[1]["summary"])
            self.assertEqual(lines[0].get("runId"), lines[1].get("runId"))

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
            day_file = next(runs.glob("2*-*-*.jsonl"))
            lines = [
                json.loads(line)
                for line in day_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(lines[0]["status"], "started")
            self.assertEqual(lines[1]["status"], "error")
            self.assertIn("124", lines[1]["summary"])
            self.assertEqual(lines[0].get("runId"), lines[1].get("runId"))

            log_text = lifecycle_log.read_text(encoding="utf-8")
            self.assertIn("finish test-issue-uuid error", log_text)
        finally:
            subprocess.run(["rm", "-rf", str(tmp)], check=False)

    def test_alpha_uses_deterministic_script_path(self):
        tmp, lifecycle_log = self._seed_temp_workspace(0)
        try:
            det_log = tmp / "alpha-det.log"
            self._write_stub(
                tmp / "tools" / "alpha-polymarket-deterministic.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf 'deterministic called\\n' >> "{det_log}"
                    printf '%s\\n' '{{"decisionAction":"skip","selectionSource":"deterministic-test"}}'
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(tmp)
            env["PATH"] = f"{tmp / 'bin'}:{env.get('PATH', '')}"
            env["OPENCLAW_BIN"] = str(tmp / "bin" / "openclaw")
            result = subprocess.run(
                ["bash", str(self.wrapper), "alpha-polymarket", "alpha"],
                cwd=str(tmp),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(det_log.exists(), "deterministic alpha script should run")

            day_file = next((tmp / "data" / "cron-runs").glob("*.jsonl"))
            lines = [
                json.loads(line)
                for line in day_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(lines[0]["status"], "started")
            self.assertEqual(lines[1]["status"], "ok")
            self.assertIn("finish test-issue-uuid ok", lifecycle_log.read_text(encoding="utf-8"))
        finally:
            subprocess.run(["rm", "-rf", str(tmp)], check=False)

    def test_orchestrator_skips_when_job_lock_exists(self):
        tmp, lifecycle_log = self._seed_temp_workspace(0)
        try:
            lock_dir = tmp / ".openclaw" / "locks" / "cron-core-grok-daily-brief.lock"
            lock_dir.mkdir(parents=True, exist_ok=True)

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
            day_file = next(runs.glob("*.jsonl"))
            lines = [
                json.loads(line)
                for line in day_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(lines), 1)
            self.assertEqual(lines[0]["status"], "skipped")
            self.assertIn("already running", lines[0]["summary"])
            self.assertFalse(lifecycle_log.exists(), "Paperclip lifecycle should not run when lock exists")
        finally:
            subprocess.run(["rm", "-rf", str(tmp)], check=False)

    def test_orchestrator_marks_error_when_evidence_repairs_are_needed(self):
        tmp, lifecycle_log = self._seed_temp_workspace(0)
        try:
            evidence_path = tmp / "data" / "workflow-health" / "evidence" / "grok-daily-brief-test-run.json"
            self._write_stub(
                tmp / "tools" / "cron-workflow-evidence.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    mkdir -p "{evidence_path.parent}"
                    cat > "{evidence_path}" <<'JSON'
                    {{"job":"grok-daily-brief","runId":"test-run","maxSeverity":"error","repairs":["posted_fallback_daily_brief"]}}
                    JSON
                    printf '%s\\n' "{evidence_path}"
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(tmp)
            env["PATH"] = f"{tmp / 'bin'}:{env.get('PATH', '')}"
            env["OPENCLAW_BIN"] = str(tmp / "bin" / "openclaw")
            env["CRON_RUN_ID"] = "test-run"
            result = subprocess.run(
                ["bash", str(self.wrapper), "grok-daily-brief", "grok"],
                cwd=str(tmp),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            day_file = next((tmp / "data" / "cron-runs").glob("*.jsonl"))
            lines = [
                json.loads(line)
                for line in day_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(lines[0]["status"], "started")
            self.assertEqual(lines[1]["status"], "error")
            self.assertIn("evidence repairs applied", lines[1]["summary"])

            log_text = lifecycle_log.read_text(encoding="utf-8")
            self.assertIn("finish test-issue-uuid error", log_text)
        finally:
            subprocess.run(["rm", "-rf", str(tmp)], check=False)


    def test_orchestrator_fails_fast_when_runtime_payload_message_missing(self):
        """Pre-flight check must abort with exit 3 when OpenClaw runtime config
        has the job but its payload.message is empty — the exact failure mode that
        caused grok-daily-brief to run empty agent turns."""
        tmp, lifecycle_log = self._seed_temp_workspace(0)
        try:
            # Create a runtime config with missing message (reproduces the bug)
            openclaw_cron_dir = tmp / ".openclaw-home" / ".openclaw" / "cron"
            openclaw_cron_dir.mkdir(parents=True)
            runtime_config = {
                "version": 1,
                "jobs": [
                    {
                        "id": "1",
                        "name": "grok-daily-brief",
                        "schedule": {"expr": "0 8 * * *"},
                        "payload": {"kind": "agentTurn"},
                        "state": {},
                        "enabled": True,
                    }
                ],
            }
            (openclaw_cron_dir / "jobs.json").write_text(
                json.dumps(runtime_config), encoding="utf-8"
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(tmp)
            env["PATH"] = f"{tmp / 'bin'}:{env.get('PATH', '')}"
            env["OPENCLAW_BIN"] = str(tmp / "bin" / "openclaw")
            env["OPENCLAW_CRON_JOBS_PATH"] = str(openclaw_cron_dir / "jobs.json")
            result = subprocess.run(
                ["bash", str(self.wrapper), "grok-daily-brief", "grok"],
                cwd=str(tmp),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 3, msg=result.stderr or result.stdout)
            self.assertIn("missing payload", result.stderr.lower() + result.stdout.lower())
            self.assertIn("auto-sync", result.stderr.lower())
            # Paperclip lifecycle should NOT have started
            self.assertFalse(lifecycle_log.exists())
        finally:
            subprocess.run(["rm", "-rf", str(tmp)], check=False)

    def test_orchestrator_proceeds_when_runtime_payload_message_present(self):
        """Pre-flight check passes when runtime config has a valid message."""
        tmp, lifecycle_log = self._seed_temp_workspace(0)
        try:
            openclaw_cron_dir = tmp / ".openclaw-home" / ".openclaw" / "cron"
            openclaw_cron_dir.mkdir(parents=True)
            runtime_config = {
                "version": 1,
                "jobs": [
                    {
                        "id": "9c1b0a7d4e2f1001",
                        "name": "grok-daily-brief",
                        "schedule": {"expr": "0 8 * * *"},
                        "payload": {
                            "kind": "agentTurn",
                            "message": "./tools/cron-core-workflow-run.sh grok-daily-brief grok",
                        },
                        "state": {},
                        "enabled": True,
                    }
                ],
            }
            (openclaw_cron_dir / "jobs.json").write_text(
                json.dumps(runtime_config), encoding="utf-8"
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(tmp)
            env["PATH"] = f"{tmp / 'bin'}:{env.get('PATH', '')}"
            env["OPENCLAW_BIN"] = str(tmp / "bin" / "openclaw")
            env["OPENCLAW_CRON_JOBS_PATH"] = str(openclaw_cron_dir / "jobs.json")
            result = subprocess.run(
                ["bash", str(self.wrapper), "grok-daily-brief", "grok"],
                cwd=str(tmp),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(lifecycle_log.exists(), "Paperclip lifecycle should have run")
        finally:
            subprocess.run(["rm", "-rf", str(tmp)], check=False)


if __name__ == "__main__":
    unittest.main()

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class GrokClawDoctorTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "grokclaw-doctor.sh"

    def _write_executable(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def _build_doctor_workspace(self, tmp: Path, *, audit_exit: int = 1, audit_output: str = "alpha-polymarket missing research markdown"):
        """Set up a temp workspace with stubs for all doctor external deps."""
        home = tmp / "home"
        workspace = tmp / "workspace"
        tools_dir = workspace / "tools"
        stubs_bin = tmp / "stubs"
        health_log = workspace / "health.log"

        self._write_executable(
            tools_dir / "telegram-post.sh",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                set -eu
                printf '%s\\n' "$*" >> "{health_log}"
                """
            ),
        )
        self._write_executable(
            tools_dir / "cron-jobs-tool.py",
            "#!/usr/bin/env python3\nimport sys; sys.exit(0)\n",
        )
        self._write_executable(
            tools_dir / "_workflow_health.py",
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import json, sys
                if sys.argv[1] == "audit-quick":
                    print(json.dumps({{
                        "healthy": {repr(audit_exit == 0)},
                        "failures": [] if {audit_exit} == 0 else [{{"message": "{audit_output}"}}],
                    }}))
                    sys.exit(0)
                if sys.argv[1] == "audit":
                    print(json.dumps({{
                        "healthy": {repr(audit_exit == 0)},
                        "failureHash": "abc123",
                        "alertMessage": "Workflow health failure: {audit_output}" if {audit_exit} != 0 else "Workflow health: healthy",
                        "draft": None if {audit_exit} == 0 else {{
                            "id": "workflow-health-abc123",
                            "title": "Fix workflow health failure in core cron workflows",
                            "description": "Problem and acceptance criteria",
                        }},
                    }}))
                    sys.exit(0)
                sys.exit(1)
                """
            ),
        )
        self._write_executable(
            tools_dir / "_workflow_health_handle.py",
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import json
                import sys
                payload = json.load(sys.stdin)
                with open("{health_log}", "a", encoding="utf-8") as handle:
                    handle.write(f"health {{payload.get('alertMessage', '')}}\\n")
                """
            ),
        )
        self._write_executable(
            tools_dir / "gateway-ctl.sh",
            "#!/bin/sh\nexit 0\n",
        )
        self._write_executable(
            tools_dir / "sync-cron-jobs.sh",
            "#!/bin/sh\nexit 0\n",
        )

        stubs_bin.mkdir(parents=True, exist_ok=True)
        self._write_executable(
            stubs_bin / "curl",
            "#!/bin/sh\nexit 0\n",
        )
        self._write_executable(
            stubs_bin / "launchctl",
            textwrap.dedent(
                """\
                #!/bin/sh
                echo "com.grokclaw.gateway"
                echo "com.grokclaw.paperclip"
                """
            ),
        )
        self._write_executable(
            stubs_bin / "crontab",
            '#!/bin/sh\necho "*/5 * * * * health-check.sh"\n',
        )
        self._write_executable(
            stubs_bin / "openclaw",
            "#!/bin/sh\nexit 0\n",
        )

        cron_dir = workspace / "cron"
        cron_dir.mkdir(parents=True, exist_ok=True)
        (cron_dir / "jobs.json").write_text('{"jobs":[]}', encoding="utf-8")
        rt_dir = home / ".openclaw" / "cron"
        rt_dir.mkdir(parents=True, exist_ok=True)
        (rt_dir / "jobs.json").write_text('{"jobs":[]}', encoding="utf-8")

        return home, workspace, health_log, stubs_bin

    def test_doctor_alerts_on_workflow_health_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            home, workspace, health_log, stubs_bin = self._build_doctor_workspace(
                tmp,
                audit_exit=1,
                audit_output="alpha-polymarket missing research markdown",
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{stubs_bin}:{env.get('PATH', '')}"
            env["TELEGRAM_BOT_TOKEN"] = "test-token"

            result = subprocess.run(
                ["sh", str(self.script), "--check"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1, msg=result.stderr or result.stdout)
            alert_text = health_log.read_text(encoding="utf-8")
            self.assertIn("health Workflow health failure: alpha-polymarket missing research markdown", alert_text)

    def test_doctor_healthy_when_audit_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            home, workspace, health_log, stubs_bin = self._build_doctor_workspace(
                tmp,
                audit_exit=0,
                audit_output="",
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{stubs_bin}:{env.get('PATH', '')}"
            env["TELEGRAM_BOT_TOKEN"] = "test-token"

            result = subprocess.run(
                ["sh", str(self.script), "--check"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("All checks passed", result.stdout)
            self.assertFalse(
                health_log.exists(),
                "No Telegram alert when all checks pass",
            )

    def test_doctor_escalates_quick_failure_into_full_audit_and_handler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            home = tmp / "home"
            workspace = tmp / "workspace"
            tools_dir = workspace / "tools"
            stubs_bin = tmp / "stubs"
            audit_log = workspace / "audit.log"
            handler_log = workspace / "handler.log"

            self._write_executable(
                tools_dir / "telegram-post.sh",
                "#!/bin/sh\nexit 0\n",
            )
            self._write_executable(
                tools_dir / "cron-jobs-tool.py",
                "#!/usr/bin/env python3\nimport sys; sys.exit(0)\n",
            )
            self._write_executable(
                tools_dir / "_workflow_health.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import json, sys
                    with open("{audit_log}", "a", encoding="utf-8") as handle:
                        handle.write(" ".join(sys.argv[1:]) + "\\n")
                    if sys.argv[1] == "audit-quick":
                        print(json.dumps({{"healthy": False, "failures": [{{"message": "alpha missing run"}}]}}))
                    elif sys.argv[1] == "audit":
                        print(json.dumps({{
                            "healthy": False,
                            "failureHash": "abc123",
                            "alertMessage": "Workflow health failure: alpha missing run",
                            "draft": {{
                                "id": "workflow-health-abc123",
                                "title": "Fix workflow health failure in core cron workflows",
                                "description": "Problem and acceptance criteria"
                            }}
                        }}))
                    else:
                        raise SystemExit(1)
                    """
                ),
            )
            self._write_executable(
                tools_dir / "_workflow_health_handle.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import sys
                    with open("{handler_log}", "a", encoding="utf-8") as handle:
                        handle.write(sys.stdin.read())
                    """
                ),
            )
            self._write_executable(tools_dir / "gateway-ctl.sh", "#!/bin/sh\nexit 0\n")
            self._write_executable(tools_dir / "sync-cron-jobs.sh", "#!/bin/sh\nexit 0\n")

            stubs_bin.mkdir(parents=True, exist_ok=True)
            self._write_executable(stubs_bin / "curl", "#!/bin/sh\nexit 0\n")
            self._write_executable(
                stubs_bin / "launchctl",
                '#!/bin/sh\necho "com.grokclaw.gateway"\necho "com.grokclaw.paperclip"\n',
            )
            self._write_executable(stubs_bin / "crontab", '#!/bin/sh\necho "*/5 * * * * health-check.sh"\n')
            self._write_executable(stubs_bin / "openclaw", "#!/bin/sh\nexit 0\n")

            cron_dir = workspace / "cron"
            cron_dir.mkdir(parents=True, exist_ok=True)
            (cron_dir / "jobs.json").write_text('{"jobs":[]}', encoding="utf-8")
            rt_dir = home / ".openclaw" / "cron"
            rt_dir.mkdir(parents=True, exist_ok=True)
            (rt_dir / "jobs.json").write_text('{"jobs":[]}', encoding="utf-8")

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{stubs_bin}:{env.get('PATH', '')}"
            env["TELEGRAM_BOT_TOKEN"] = "test-token"

            result = subprocess.run(
                ["sh", str(self.script), "--check"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1, msg=result.stderr or result.stdout)
            self.assertTrue(audit_log.exists(), "doctor should invoke workflow health audit commands")
            self.assertIn("audit-quick", audit_log.read_text(encoding="utf-8"))
            self.assertIn("audit", audit_log.read_text(encoding="utf-8"))
            self.assertTrue(handler_log.exists(), "doctor should hand full-audit payload to the handler")
            self.assertIn('"failureHash": "abc123"', handler_log.read_text(encoding="utf-8"))

    def test_doctor_escalates_full_audit_when_quick_check_is_green_but_contract_is_broken(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            home = tmp / "home"
            workspace = tmp / "workspace"
            tools_dir = workspace / "tools"
            stubs_bin = tmp / "stubs"
            audit_log = workspace / "audit.log"
            handler_log = workspace / "handler.log"

            self._write_executable(tools_dir / "telegram-post.sh", "#!/bin/sh\nexit 0\n")
            self._write_executable(tools_dir / "cron-jobs-tool.py", "#!/usr/bin/env python3\nimport sys; sys.exit(0)\n")
            self._write_executable(
                tools_dir / "_workflow_health.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import json, sys
                    with open("{audit_log}", "a", encoding="utf-8") as handle:
                        handle.write(" ".join(sys.argv[1:]) + "\\n")
                    if sys.argv[1] == "audit-quick":
                        print(json.dumps({{"healthy": True, "failures": []}}))
                    elif sys.argv[1] == "audit":
                        print(json.dumps({{
                            "healthy": False,
                            "failureHash": "deep123",
                            "alertMessage": "Workflow health failure: alpha issue left open",
                            "draft": {{
                                "id": "workflow-health-deep123",
                                "title": "Fix workflow health failure in core cron workflows",
                                "description": "Problem and acceptance criteria"
                            }}
                        }}))
                    else:
                        raise SystemExit(1)
                    """
                ),
            )
            self._write_executable(
                tools_dir / "_workflow_health_handle.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import sys
                    with open("{handler_log}", "a", encoding="utf-8") as handle:
                        handle.write(sys.stdin.read())
                    """
                ),
            )
            self._write_executable(tools_dir / "gateway-ctl.sh", "#!/bin/sh\nexit 0\n")
            self._write_executable(tools_dir / "sync-cron-jobs.sh", "#!/bin/sh\nexit 0\n")

            stubs_bin.mkdir(parents=True, exist_ok=True)
            self._write_executable(stubs_bin / "curl", "#!/bin/sh\nexit 0\n")
            self._write_executable(
                stubs_bin / "launchctl",
                '#!/bin/sh\necho "com.grokclaw.gateway"\necho "com.grokclaw.paperclip"\n',
            )
            self._write_executable(stubs_bin / "crontab", '#!/bin/sh\necho "*/5 * * * * health-check.sh"\n')
            self._write_executable(stubs_bin / "openclaw", "#!/bin/sh\nexit 0\n")

            cron_dir = workspace / "cron"
            cron_dir.mkdir(parents=True, exist_ok=True)
            (cron_dir / "jobs.json").write_text('{"jobs":[]}', encoding="utf-8")
            rt_dir = home / ".openclaw" / "cron"
            rt_dir.mkdir(parents=True, exist_ok=True)
            (rt_dir / "jobs.json").write_text('{"jobs":[]}', encoding="utf-8")

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{stubs_bin}:{env.get('PATH', '')}"
            env["TELEGRAM_BOT_TOKEN"] = "test-token"

            result = subprocess.run(
                ["sh", str(self.script), "--check"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1, msg=result.stderr or result.stdout)
            log_text = audit_log.read_text(encoding="utf-8")
            self.assertIn("audit-quick", log_text)
            self.assertIn("audit", log_text)
            self.assertTrue(handler_log.exists(), "doctor should still escalate the deep failure")
            self.assertIn('"failureHash": "deep123"', handler_log.read_text(encoding="utf-8"))

    def test_doctor_heal_restores_two_minute_health_check_crontab(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            home = tmp / "home"
            workspace = tmp / "workspace"
            tools_dir = workspace / "tools"
            stubs_bin = tmp / "stubs"
            crontab_log = workspace / "crontab.log"

            self._write_executable(tools_dir / "telegram-post.sh", "#!/bin/sh\nexit 0\n")
            self._write_executable(tools_dir / "cron-jobs-tool.py", "#!/usr/bin/env python3\nimport sys; sys.exit(0)\n")
            self._write_executable(
                tools_dir / "_workflow_health.py",
                '#!/usr/bin/env python3\nimport json\nprint(json.dumps({"healthy": True, "failures": [], "alertMessage": "Workflow health: healthy", "draft": None}))\n',
            )
            self._write_executable(tools_dir / "_workflow_health_handle.py", "#!/usr/bin/env python3\nimport sys\nsys.stdin.read()\n")
            self._write_executable(tools_dir / "gateway-ctl.sh", "#!/bin/sh\nexit 0\n")
            self._write_executable(tools_dir / "sync-cron-jobs.sh", "#!/bin/sh\nexit 0\n")

            stubs_bin.mkdir(parents=True, exist_ok=True)
            self._write_executable(stubs_bin / "curl", "#!/bin/sh\nexit 0\n")
            self._write_executable(
                stubs_bin / "launchctl",
                '#!/bin/sh\necho "com.grokclaw.gateway"\necho "com.grokclaw.paperclip"\n',
            )
            self._write_executable(
                stubs_bin / "crontab",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    if [ "$1" = "-l" ]; then
                      exit 0
                    fi
                    cat > "{crontab_log}"
                    """
                ),
            )
            self._write_executable(stubs_bin / "openclaw", "#!/bin/sh\nexit 0\n")

            cron_dir = workspace / "cron"
            cron_dir.mkdir(parents=True, exist_ok=True)
            (cron_dir / "jobs.json").write_text('{"jobs":[]}', encoding="utf-8")
            rt_dir = home / ".openclaw" / "cron"
            rt_dir.mkdir(parents=True, exist_ok=True)
            (rt_dir / "jobs.json").write_text('{"jobs":[]}', encoding="utf-8")

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(workspace)
            env["PATH"] = f"{stubs_bin}:{env.get('PATH', '')}"
            env["TELEGRAM_BOT_TOKEN"] = "test-token"

            result = subprocess.run(
                ["sh", str(self.script), "--heal"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("*/2 * * * *", crontab_log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

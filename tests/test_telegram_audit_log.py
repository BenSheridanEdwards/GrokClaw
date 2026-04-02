import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class TelegramAuditLogTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.post_script = self.workspace / "tools" / "telegram-post.sh"
        self.inline_script = self.workspace / "tools" / "telegram-inline.sh"

    def _write_executable(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_telegram_post_writes_audit_log_after_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            self._write_executable(
                tools_dir / "_telegram_post.py",
                "#!/usr/bin/env python3\nprint('ok')\n",
            )
            self._write_executable(
                tools_dir / "_audit_log.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import datetime as dt
                    import json
                    import os
                    from pathlib import Path
                    import sys

                    now = dt.datetime.strptime(os.environ["WORKFLOW_HEALTH_NOW"], "%Y-%m-%dT%H:%M:%SZ")
                    path = Path(os.environ["WORKSPACE_ROOT"]) / "data" / "audit-log" / f"{now.strftime('%Y-%m-%d')}.jsonl"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps({"kind": sys.argv[1], "topic": sys.argv[2], "message": sys.argv[3], "topicId": sys.argv[4]}) + "\\n")
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["TELEGRAM_BOT_TOKEN"] = "token"
            env["TELEGRAM_GROUP_ID"] = "group"
            env["WORKFLOW_HEALTH_NOW"] = "2026-04-01T10:00:00Z"

            result = subprocess.run(
                ["sh", str(self.post_script), "health", "OpenClaw research (morning): all good"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            audit_file = workspace / "data" / "audit-log" / "2026-04-01.jsonl"
            self.assertTrue(audit_file.exists())

    def test_telegram_post_uses_telegram_message_env_when_no_body_arg(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            self._write_executable(
                tools_dir / "_telegram_post.py",
                "#!/usr/bin/env python3\nprint('ok')\n",
            )
            self._write_executable(
                tools_dir / "_audit_log.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import datetime as dt
                    import json
                    import os
                    from pathlib import Path
                    import sys

                    now = dt.datetime.strptime(os.environ["WORKFLOW_HEALTH_NOW"], "%Y-%m-%dT%H:%M:%SZ")
                    path = Path(os.environ["WORKSPACE_ROOT"]) / "data" / "audit-log" / f"{now.strftime('%Y-%m-%d')}.jsonl"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps({"kind": sys.argv[1], "topic": sys.argv[2], "message": sys.argv[3], "topicId": sys.argv[4]}) + "\\n")
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["TELEGRAM_BOT_TOKEN"] = "token"
            env["TELEGRAM_GROUP_ID"] = "group"
            env["WORKFLOW_HEALTH_NOW"] = "2026-04-01T10:00:00Z"
            env["TELEGRAM_MESSAGE"] = "Alpha: spot at $1,100 and $5 edge"

            result = subprocess.run(
                ["sh", str(self.post_script), "health"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            audit_file = workspace / "data" / "audit-log" / "2026-04-01.jsonl"
            records = [json.loads(line) for line in audit_file.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(records[0]["message"], "Alpha: spot at $1,100 and $5 edge")

    def test_telegram_inline_writes_audit_log_after_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            self._write_executable(
                tools_dir / "_telegram_inline.py",
                "#!/usr/bin/env python3\nprint('ok')\n",
            )
            self._write_executable(
                tools_dir / "retry.sh",
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    while [ "$#" -gt 0 ]; do
                      case "$1" in
                        --) shift; break ;;
                        *) shift ;;
                      esac
                    done
                    exec "$@"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "_audit_log.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import datetime as dt
                    import json
                    import os
                    from pathlib import Path
                    import sys

                    now = dt.datetime.strptime(os.environ["WORKFLOW_HEALTH_NOW"], "%Y-%m-%dT%H:%M:%SZ")
                    path = Path(os.environ["WORKSPACE_ROOT"]) / "data" / "audit-log" / f"{now.strftime('%Y-%m-%d')}.jsonl"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps({"kind": sys.argv[1], "topic": sys.argv[2], "message": sys.argv[3], "topicId": sys.argv[4]}) + "\\n")
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["TELEGRAM_BOT_TOKEN"] = "token"
            env["TELEGRAM_GROUP_ID"] = "group"
            env["WORKFLOW_HEALTH_NOW"] = "2026-04-01T10:00:00Z"

            result = subprocess.run(
                ["sh", str(self.inline_script), "suggestions", "Daily Suggestion #11: Fix workflow health", '[{"text":"Approve","callback_data":"approve:1"}]', "plain"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            audit_file = workspace / "data" / "audit-log" / "2026-04-01.jsonl"
            self.assertTrue(audit_file.exists())
            records = [json.loads(line) for line in audit_file.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(records[0]["kind"], "telegram_inline")
            self.assertEqual(records[0]["topic"], "suggestions")

    def test_telegram_post_writes_failure_audit_log_when_delivery_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            self._write_executable(
                tools_dir / "_telegram_post.py",
                "#!/usr/bin/env python3\nimport sys\nprint('ERROR: boom', file=sys.stderr)\nsys.exit(1)\n",
            )
            self._write_executable(
                tools_dir / "_audit_log.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import datetime as dt
                    import json
                    import os
                    from pathlib import Path
                    import sys

                    now = dt.datetime.strptime(os.environ["WORKFLOW_HEALTH_NOW"], "%Y-%m-%dT%H:%M:%SZ")
                    path = Path(os.environ["WORKSPACE_ROOT"]) / "data" / "audit-log" / f"{now.strftime('%Y-%m-%d')}.jsonl"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps({"kind": sys.argv[1], "topic": sys.argv[2], "message": sys.argv[3], "topicId": sys.argv[4]}) + "\\n")
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["TELEGRAM_BOT_TOKEN"] = "token"
            env["TELEGRAM_GROUP_ID"] = "group"
            env["WORKFLOW_HEALTH_NOW"] = "2026-04-01T10:00:00Z"

            result = subprocess.run(
                ["sh", str(self.post_script), "health", "OpenClaw research (morning): all good"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            audit_file = workspace / "data" / "audit-log" / "2026-04-01.jsonl"
            self.assertTrue(audit_file.exists())
            records = [json.loads(line) for line in audit_file.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(records[0]["kind"], "telegram_post_failed")
            self.assertEqual(records[0]["topic"], "health")

    def test_telegram_inline_writes_failure_audit_log_when_delivery_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools_dir = workspace / "tools"
            self._write_executable(
                tools_dir / "_telegram_inline.py",
                "#!/usr/bin/env python3\nimport sys\nprint('ERROR: boom', file=sys.stderr)\nsys.exit(1)\n",
            )
            self._write_executable(
                tools_dir / "retry.sh",
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    while [ "$#" -gt 0 ]; do
                      case "$1" in
                        --) shift; break ;;
                        *) shift ;;
                      esac
                    done
                    exec "$@"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "_audit_log.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import datetime as dt
                    import json
                    import os
                    from pathlib import Path
                    import sys

                    now = dt.datetime.strptime(os.environ["WORKFLOW_HEALTH_NOW"], "%Y-%m-%dT%H:%M:%SZ")
                    path = Path(os.environ["WORKSPACE_ROOT"]) / "data" / "audit-log" / f"{now.strftime('%Y-%m-%d')}.jsonl"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps({"kind": sys.argv[1], "topic": sys.argv[2], "message": sys.argv[3], "topicId": sys.argv[4]}) + "\\n")
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["TELEGRAM_BOT_TOKEN"] = "token"
            env["TELEGRAM_GROUP_ID"] = "group"
            env["WORKFLOW_HEALTH_NOW"] = "2026-04-01T10:00:00Z"

            result = subprocess.run(
                ["sh", str(self.inline_script), "suggestions", "Daily Suggestion #11: Fix workflow health", '[{"text":"Approve","callback_data":"approve:1"}]', "plain"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            audit_file = workspace / "data" / "audit-log" / "2026-04-01.jsonl"
            self.assertTrue(audit_file.exists())
            records = [json.loads(line) for line in audit_file.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(records[0]["kind"], "telegram_inline_failed")
            self.assertEqual(records[0]["topic"], "suggestions")


if __name__ == "__main__":
    unittest.main()

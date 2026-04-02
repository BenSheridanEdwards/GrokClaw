import os
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class DispatchActionIdempotencyTests(unittest.TestCase):
    def test_duplicate_action_token_is_ignored(self):
        workspace = Path(__file__).resolve().parents[1]
        script = workspace / "tools" / "dispatch-telegram-action.sh"

        with tempfile.TemporaryDirectory() as tmp_home:
            env = os.environ.copy()
            env["HOME"] = tmp_home
            env["WORKSPACE_ROOT"] = str(workspace)

            first = subprocess.run(
                ["sh", str(script), "Run Probe | probe:single-poller:dup1"],
                env=env,
                cwd=str(workspace),
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("Probe action received", first.stdout)

            second = subprocess.run(
                ["sh", str(script), "Run Probe | probe:single-poller:dup1"],
                env=env,
                cwd=str(workspace),
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("Action already processed, skipping", second.stdout)

            third = subprocess.run(
                ["sh", str(script), "Run Probe | probe:single-poller:dup2"],
                env=env,
                cwd=str(workspace),
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("Probe action received", third.stdout)

    def test_incoming_action_is_audit_logged(self):
        workspace = Path(__file__).resolve().parents[1]
        script = workspace / "tools" / "dispatch-telegram-action.sh"

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / "home"
            fake_workspace = Path(tmpdir) / "workspace"
            tools_dir = fake_workspace / "tools"
            tools_dir.mkdir(parents=True, exist_ok=True)

            (tools_dir / "_audit_log.py").write_text(
                (
                    "#!/usr/bin/env python3\n"
                    "import json\n"
                    "import os\n"
                    "import sys\n"
                    "from pathlib import Path\n"
                    "path = Path(os.environ['WORKSPACE_ROOT']) / 'data' / 'audit-log' / 'incoming.jsonl'\n"
                    "path.parent.mkdir(parents=True, exist_ok=True)\n"
                    "with path.open('a', encoding='utf-8') as handle:\n"
                    "    handle.write(json.dumps({'kind': sys.argv[1], 'topic': sys.argv[2], 'message': sys.argv[3], 'topicId': sys.argv[4] if len(sys.argv) > 4 else ''}) + '\\n')\n"
                ),
                encoding="utf-8",
            )
            (tools_dir / "_audit_log.py").chmod(0o755)

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(fake_workspace)

            result = subprocess.run(
                ["sh", str(script), "Run Probe | probe:single-poller:audit1"],
                env=env,
                cwd=str(workspace),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            audit_file = fake_workspace / "data" / "audit-log" / "incoming.jsonl"
            self.assertTrue(audit_file.exists())
            rows = [json.loads(line) for line in audit_file.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["kind"], "telegram_incoming")
            self.assertEqual(rows[0]["topic"], "actions")
            self.assertEqual(rows[0]["message"], "Run Probe | probe:single-poller:audit1")

    def test_duplicate_incoming_action_is_still_audit_logged(self):
        workspace = Path(__file__).resolve().parents[1]
        script = workspace / "tools" / "dispatch-telegram-action.sh"

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / "home"
            fake_workspace = Path(tmpdir) / "workspace"
            tools_dir = fake_workspace / "tools"
            tools_dir.mkdir(parents=True, exist_ok=True)

            (tools_dir / "_audit_log.py").write_text(
                (
                    "#!/usr/bin/env python3\n"
                    "import json\n"
                    "import os\n"
                    "import sys\n"
                    "from pathlib import Path\n"
                    "path = Path(os.environ['WORKSPACE_ROOT']) / 'data' / 'audit-log' / 'incoming.jsonl'\n"
                    "path.parent.mkdir(parents=True, exist_ok=True)\n"
                    "with path.open('a', encoding='utf-8') as handle:\n"
                    "    handle.write(json.dumps({'kind': sys.argv[1], 'topic': sys.argv[2], 'message': sys.argv[3], 'topicId': sys.argv[4] if len(sys.argv) > 4 else ''}) + '\\n')\n"
                ),
                encoding="utf-8",
            )
            (tools_dir / "_audit_log.py").chmod(0o755)

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(fake_workspace)

            for _ in range(2):
                subprocess.run(
                    ["sh", str(script), "Run Probe | probe:single-poller:audit2"],
                    env=env,
                    cwd=str(workspace),
                    capture_output=True,
                    text=True,
                    check=False,
                )

            audit_file = fake_workspace / "data" / "audit-log" / "incoming.jsonl"
            self.assertTrue(audit_file.exists())
            rows = [json.loads(line) for line in audit_file.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["kind"] == "telegram_incoming" for row in rows))


if __name__ == "__main__":
    unittest.main()

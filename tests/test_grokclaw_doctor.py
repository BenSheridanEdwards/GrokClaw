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

    def test_doctor_alerts_and_requests_linear_draft_on_new_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            home = tmp / "home"
            workspace = tmp / "workspace"
            tools_dir = workspace / "tools"
            health_log = workspace / "health.log"
            draft_log = workspace / "draft.log"

            audit_payload = {
                "healthy": False,
                "failureHash": "abc123",
                "alertMessage": "Workflow health failure: alpha-polymarket missing research markdown",
                "failures": [{"workflow": "alpha-polymarket", "message": "missing research markdown"}],
                "draft": {
                    "id": "workflow-health-abc123",
                    "title": "Fix workflow health failure",
                    "description": "Problem and acceptance criteria",
                },
            }

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
                tools_dir / "linear-draft-approval.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{draft_log}"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "_workflow_health.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import json
                    payload = {audit_payload!r}
                    print(json.dumps(payload))
                    """
                ),
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(workspace)

            result = subprocess.run(
                ["sh", str(self.script), "--check"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1, msg=result.stderr or result.stdout)
            self.assertIn("health Workflow health failure", health_log.read_text(encoding="utf-8"))
            draft_text = draft_log.read_text(encoding="utf-8")
            self.assertIn("request workflow-health-abc123 suggestion abc123 suggestions Fix workflow health failure Problem and acceptance criteria In Progress", draft_text)

    def test_doctor_dedupes_same_failure_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            home = tmp / "home"
            workspace = tmp / "workspace"
            tools_dir = workspace / "tools"
            health_log = workspace / "health.log"
            draft_log = workspace / "draft.log"

            audit_payload = {
                "healthy": False,
                "failureHash": "samehash",
                "alertMessage": "Workflow health failure: repeated",
                "failures": [{"workflow": "alpha-polymarket", "message": "repeated"}],
                "draft": {
                    "id": "workflow-health-samehash",
                    "title": "Fix workflow health failure",
                    "description": "Problem and acceptance criteria",
                },
            }

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
                tools_dir / "linear-draft-approval.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{draft_log}"
                    """
                ),
            )
            self._write_executable(
                tools_dir / "_workflow_health.py",
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import json
                    payload = {audit_payload!r}
                    print(json.dumps(payload))
                    """
                ),
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["WORKSPACE_ROOT"] = str(workspace)

            first = subprocess.run(
                ["sh", str(self.script), "--check"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            second = subprocess.run(
                ["sh", str(self.script), "--check"],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(first.returncode, 1)
            self.assertEqual(second.returncode, 1)
            self.assertEqual(health_log.read_text(encoding="utf-8").count("health Workflow health failure"), 1)
            self.assertEqual(draft_log.read_text(encoding="utf-8").count("request workflow-health-samehash"), 1)


if __name__ == "__main__":
    unittest.main()

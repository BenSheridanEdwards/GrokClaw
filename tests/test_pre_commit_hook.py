import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class PreCommitHookTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.hook = self.workspace / ".husky" / "pre-commit"
        self.runner = self.workspace / "tools" / "test-all.sh"

    def test_husky_pre_commit_hook_runs_full_test_suite(self):
        self.assertTrue(self.hook.exists(), "expected .husky/pre-commit hook")
        content = self.hook.read_text(encoding="utf-8")
        self.assertIn("tools/test-all.sh", content)

    def test_test_all_runner_invokes_expected_steps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            bin_dir = tmp / "bin"
            call_log = tmp / "calls.log"
            fake_tools = tmp / "workspace" / "tools"
            fake_tools.mkdir(parents=True)

            (fake_tools / "dummy.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            (fake_tools / "_dummy.py").write_text("", encoding="utf-8")

            stub = textwrap.dedent(
                f"""\
                #!/bin/sh
                set -eu
                printf '%s\\n' "$*" >> "{call_log}"
                exit 0
                """
            )
            py_stub = bin_dir / "python3"
            py_stub.parent.mkdir(parents=True, exist_ok=True)
            py_stub.write_text(stub, encoding="utf-8")
            py_stub.chmod(0o755)

            e2e_stub = fake_tools / "reliability-e2e.sh"
            e2e_stub.write_text(
                f"#!/bin/sh\nprintf 'reliability-e2e\\n' >> \"{call_log}\"\n",
                encoding="utf-8",
            )
            e2e_stub.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            env["WORKSPACE_ROOT"] = str(tmp / "workspace")

            result = subprocess.run(
                ["sh", str(self.runner)],
                cwd=str(self.workspace),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            invoked = call_log.read_text(encoding="utf-8")
            self.assertIn("-m py_compile", invoked)
            self.assertIn("-m unittest discover", invoked)
            self.assertIn("reliability-e2e", invoked)


if __name__ == "__main__":
    unittest.main()

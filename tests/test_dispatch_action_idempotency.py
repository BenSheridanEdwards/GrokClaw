import os
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


if __name__ == "__main__":
    unittest.main()

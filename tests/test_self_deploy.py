import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


def _git_init(repo):
    subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(repo),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(repo),
        capture_output=True,
        check=True,
    )


class TestSelfDeployScript(unittest.TestCase):
    """Tests for self-deploy.sh"""

    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]
        self.script = self.workspace / "tools" / "self-deploy.sh"

    def _write_dummy_env(self, repo):
        env_file = repo / ".env"
        env_file.write_text(
            "OPENCLAW_API_KEY=test\n"
            # cron-jobs-tool validate expands ${TELEGRAM_GROUP_ID} in jobs.json
            "TELEGRAM_GROUP_ID=-1001234567890\n",
            encoding="utf-8",
        )
        return env_file

    def _copy_tool(self, repo, name):
        src = self.workspace / "tools" / name
        dst = repo / "tools" / name
        if src.exists():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            dst.chmod(0o755)

    def test_validate_failure_blocks_deploy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "cron").mkdir()
            (repo / "tools").mkdir()
            _git_init(repo)
            subprocess.run(
                ["git", "commit", "--allow-empty", "-m", "init"],
                cwd=str(repo),
                capture_output=True,
                check=True,
            )
            (repo / "cron" / "jobs.json").write_text(
                json.dumps({"version": 1}), encoding="utf-8"
            )
            tool = repo / "tools" / "cron-jobs-tool.py"
            tool.write_text(
                (self.workspace / "tools" / "cron-jobs-tool.py").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                ["sh", str(self.script)],
                capture_output=True,
                text=True,
                cwd=str(repo),
                env={**os.environ, "WORKSPACE_ROOT": str(repo)},
            )
            self.assertIn(
                "Deploy blocked",
                result.stderr,
                msg=f"expected 'Deploy blocked' in stderr, got exit {result.returncode}: {result.stderr[:200]}",
            )

    def test_clean_deploy_exits_early_when_no_new_commits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            origin = Path(tmpdir) / "origin.git"
            repo = Path(tmpdir) / "project"
            repo.mkdir()
            (repo / "cron").mkdir()
            (repo / "tools").mkdir()
            subprocess.run(
                ["git", "init", "--bare", str(origin)],
                capture_output=True,
                check=True,
            )
            _git_init(repo)
            subprocess.run(
                ["git", "commit", "--allow-empty", "-m", "initial"],
                cwd=str(repo),
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "remote", "add", "origin", str(origin)],
                cwd=str(repo),
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "push", "-u", "origin", "main"],
                cwd=str(repo),
                capture_output=True,
                check=True,
            )
            (repo / "cron" / "jobs.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "jobs": [
                            {
                                "id": "1",
                                "name": "grok-daily-brief",
                                "schedule": {"expr": "0 8 * * *"},
                                "payload": {"kind": "agentTurn"},
                                "delivery": {
                                    "mode": "announce",
                                    "channel": "telegram",
                                    "to": "${TELEGRAM_GROUP_ID}",
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self._write_dummy_env(repo)
            self._copy_tool(repo, "cron-jobs-tool.py")
            self._copy_tool(repo, "sync-cron-jobs.sh")
            self._copy_tool(repo, "gateway-ctl.sh")
            self._copy_tool(repo, "health-check.sh")
            self._copy_tool(repo, "telegram-post.sh")
            result = subprocess.run(
                ["sh", str(self.script)],
                capture_output=True,
                text=True,
                cwd=str(repo),
                env={**os.environ, "WORKSPACE_ROOT": str(repo)},
            )
            self.assertIn("No deploy needed", result.stdout + result.stderr)


class TestDeployScriptSyntax(unittest.TestCase):
    """Shell syntax validation for deploy-related scripts"""

    def test_self_deploy_script_has_valid_shell_syntax(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "self-deploy.sh"
        result = subprocess.run(
            ["sh", "-n", str(script)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_sync_cron_jobs_script_has_valid_shell_syntax(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "sync-cron-jobs.sh"
        result = subprocess.run(
            ["sh", "-n", str(script)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()

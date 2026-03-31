import json
import importlib.util
import subprocess
import unittest
from pathlib import Path


class WorkflowPromptTests(unittest.TestCase):
    @staticmethod
    def _load_module(path: Path, module_name: str):
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def test_daily_suggestion_prompt_requires_button_not_plain_approve(self):
        workspace = Path(__file__).resolve().parents[1]
        jobs_path = workspace / "cron" / "jobs.json"
        jobs = json.loads(jobs_path.read_text(encoding="utf-8")).get("jobs", [])
        daily = next(job for job in jobs if job.get("name") == "daily-grokclaw-suggestion")
        message = daily["payload"]["message"]

        self.assertIn("Approve? (tap the Approve button)", message)
        self.assertNotIn("reply exactly 'approve'", message)

    def test_repo_cron_jobs_have_no_scheduler_state(self):
        workspace = Path(__file__).resolve().parents[1]
        jobs_path = workspace / "cron" / "jobs.json"
        jobs = json.loads(jobs_path.read_text(encoding="utf-8")).get("jobs", [])
        scheduler_keys = {"state", "createdAtMs", "updatedAtMs"}
        for job in jobs:
            name = job.get("name", "?")
            found = scheduler_keys & job.keys()
            self.assertFalse(
                found,
                f"{name}: scheduler-only keys {found} must not be committed; "
                "run: python3 tools/cron-jobs-tool.py strip",
            )

    def test_cron_jobs_pass_telegram_delivery_validation(self):
        workspace = Path(__file__).resolve().parents[1]
        tool = workspace / "tools" / "cron-jobs-tool.py"
        proc = subprocess.run(
            ["python3", str(tool), "validate"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            proc.returncode,
            0,
            proc.stderr or proc.stdout or "validate failed",
        )

    def test_cron_jobs_tool_treats_agent_turn_camelcase_as_isolated_job(self):
        workspace = Path(__file__).resolve().parents[1]
        tool = workspace / "tools" / "cron-jobs-tool.py"
        module = self._load_module(tool, "cron_jobs_tool")

        jobs = {
            "jobs": [
                {
                    "name": "example",
                    "payload": {"kind": "agentTurn"},
                }
            ]
        }

        errors = module.validate_jobs(jobs)

        self.assertIn(
            "example: missing job-level delivery; "
            'use {"mode": "announce", "channel": "telegram", "to": "<group>", '
            '"bestEffort": true}',
            errors,
        )

    def test_cron_scrutiny_context_registers_agent_turn_camelcase_jobs(self):
        workspace = Path(__file__).resolve().parents[1]
        tool = workspace / "tools" / "_cron_scrutiny_context.py"
        module = self._load_module(tool, "cron_scrutiny_context")

        registered = module.load_registered_jobs(workspace)

        self.assertIn("pr-watch", registered)
        self.assertIn("grok-cron-scrutiny", registered)
        self.assertIn("alpha-daily-research", registered)


if __name__ == "__main__":
    unittest.main()

import json
import subprocess
import unittest
from pathlib import Path


class WorkflowPromptTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

import json
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


if __name__ == "__main__":
    unittest.main()

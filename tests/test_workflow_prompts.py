import json
import subprocess
import unittest
from pathlib import Path


def load_core_jobs_fixture(workspace: Path) -> list[dict]:
    fixture_path = workspace / "tests" / "fixtures" / "core-cron-jobs.json"
    return json.loads(fixture_path.read_text(encoding="utf-8")).get("jobs", [])


class WorkflowPromptTests(unittest.TestCase):
    def test_repo_cron_jobs_contain_the_three_core_workflows(self):
        workspace = Path(__file__).resolve().parents[1]
        jobs = load_core_jobs_fixture(workspace)
        names = {job.get("name") for job in jobs}
        core = {"grok-daily-brief", "grok-openclaw-research", "alpha-polymarket"}
        self.assertTrue(core.issubset(names), f"missing core workflows: {core - names}")
        self.assertNotIn("kimi-polymarket", names)
        self.assertNotIn("kimi-daily-brief", names)

    def test_three_workflow_cron_messages_invoke_orchestrator_only(self):
        workspace = Path(__file__).resolve().parents[1]
        jobs = {
            job["name"]: job
            for job in load_core_jobs_fixture(workspace)
        }

        daily_brief = jobs["grok-daily-brief"]["payload"]["message"]
        self.assertIn("./tools/cron-core-workflow-run.sh grok-daily-brief grok", daily_brief)
        self.assertNotIn("cron-paperclip-lifecycle.sh start", daily_brief)

        openclaw = jobs["grok-openclaw-research"]["payload"]["message"]
        self.assertIn("./tools/cron-core-workflow-run.sh grok-openclaw-research grok", openclaw)
        self.assertNotIn("cron-paperclip-lifecycle.sh start", openclaw)

        alpha = jobs["alpha-polymarket"]["payload"]["message"]
        self.assertIn("./tools/cron-core-workflow-run.sh alpha-polymarket alpha", alpha)
        self.assertNotIn("cron-paperclip-lifecycle.sh start", alpha)

    def test_work_prompt_files_contain_task_bodies(self):
        workspace = Path(__file__).resolve().parents[1]
        prompts = workspace / "docs" / "prompts"
        daily = (prompts / "cron-work-grok-daily-brief.md").read_text(encoding="utf-8")
        self.assertIn("Paperclip issues from the last 24 hours", daily)
        self.assertIn("audit log", daily.lower())
        self.assertIn("data/linear-creations/", daily)
        self.assertIn("user_request", daily)
        self.assertIn("./tools/telegram-suggestion.sh", daily)

        research = (prompts / "cron-work-grok-openclaw-research.md").read_text(encoding="utf-8")
        self.assertIn("morning", research.lower())
        self.assertIn("afternoon", research.lower())
        self.assertIn("evening", research.lower())
        self.assertIn("data/research/openclaw/", research)

        alpha = (prompts / "cron-work-alpha-polymarket.md").read_text(encoding="utf-8")
        self.assertIn("data/alpha/research/", alpha)
        self.assertIn("./tools/agent-report.sh alpha alpha-polymarket", alpha)

    def test_repo_cron_jobs_have_no_scheduler_state(self):
        workspace = Path(__file__).resolve().parents[1]
        jobs = load_core_jobs_fixture(workspace)
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
        fixture_path = workspace / "tests" / "fixtures" / "core-cron-jobs.json"
        proc = subprocess.run(
            ["python3", str(tool), "validate", str(fixture_path)],
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

    def test_three_core_workflows_have_expected_schedules(self):
        workspace = Path(__file__).resolve().parents[1]
        jobs = {
            job["name"]: job["schedule"]["expr"]
            for job in load_core_jobs_fixture(workspace)
        }

        self.assertEqual(jobs["grok-daily-brief"], "0 8 * * *")
        self.assertEqual(jobs["grok-openclaw-research"], "0 7,13,19 * * *")
        self.assertEqual(jobs["alpha-polymarket"], "0 * * * *")
        self.assertNotIn("kimi-polymarket", jobs)


if __name__ == "__main__":
    unittest.main()

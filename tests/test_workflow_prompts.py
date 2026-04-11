import json
import subprocess
import tempfile
import unittest
from pathlib import Path


def load_core_jobs_fixture(workspace: Path) -> list[dict]:
    fixture_path = workspace / "tests" / "fixtures" / "core-cron-jobs.json"
    return json.loads(fixture_path.read_text(encoding="utf-8")).get("jobs", [])


class WorkflowPromptTests(unittest.TestCase):
    def test_repo_cron_jobs_contain_the_two_core_workflows(self):
        workspace = Path(__file__).resolve().parents[1]
        jobs = load_core_jobs_fixture(workspace)
        names = {job.get("name") for job in jobs}
        core = {"grok-daily-brief", "alpha-polymarket"}
        self.assertTrue(core.issubset(names), f"missing core workflows: {core - names}")
        self.assertNotIn("kimi-polymarket", names)
        self.assertNotIn("kimi-daily-brief", names)

    def test_two_workflow_cron_messages_invoke_orchestrator_only(self):
        workspace = Path(__file__).resolve().parents[1]
        jobs = {
            job["name"]: job
            for job in load_core_jobs_fixture(workspace)
        }

        daily_brief = jobs["grok-daily-brief"]["payload"]["message"]
        self.assertIn("./tools/cron-core-workflow-run.sh grok-daily-brief grok", daily_brief)
        self.assertNotIn("cron-paperclip-lifecycle.sh start", daily_brief)

        alpha = jobs["alpha-polymarket"]["payload"]["message"]
        self.assertIn("./tools/cron-core-workflow-run.sh alpha-polymarket alpha", alpha)
        self.assertNotIn("cron-paperclip-lifecycle.sh start", alpha)

    def test_alpha_polymarket_disables_cron_completion_telegram_announce(self):
        """Full agent transcripts exceed Telegram 4096; hourly summary uses telegram-post.sh."""
        workspace = Path(__file__).resolve().parents[1]
        jobs = {job["name"]: job for job in load_core_jobs_fixture(workspace)}
        self.assertEqual(jobs["alpha-polymarket"]["delivery"]["mode"], "none")
        self.assertEqual(jobs["grok-daily-brief"]["delivery"]["mode"], "announce")

    def test_work_prompt_files_contain_task_bodies(self):
        workspace = Path(__file__).resolve().parents[1]
        prompts = workspace / "docs" / "prompts"
        daily = (prompts / "cron-work-grok-daily-brief.md").read_text(encoding="utf-8")
        self.assertIn("Paperclip issues from the last 24 hours", daily)
        self.assertIn("audit log", daily.lower())
        self.assertIn("data/linear-creations/", daily)
        self.assertIn("user_request", daily)
        self.assertIn("./tools/telegram-suggestion.sh", daily)

        alpha = (prompts / "cron-work-alpha-polymarket.md").read_text(encoding="utf-8")
        self.assertIn("data/alpha/research/", alpha)
        self.assertIn("./tools/agent-report.sh alpha alpha-polymarket", alpha)
        self.assertIn("Alpha · Hourly ·", alpha)
        self.assertIn("TRADE", alpha)
        self.assertIn("HOLD", alpha)
        self.assertIn("bonding-copy mode", alpha)
        self.assertIn("If no valid bonding setup, HOLD", alpha)
        self.assertNotIn("whale-copy candidate selection", alpha)

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

    def test_validate_rejects_delivery_none_for_non_whitelisted_job(self):
        workspace = Path(__file__).resolve().parents[1]
        fixture_path = workspace / "tests" / "fixtures" / "core-cron-jobs.json"
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        for job in data["jobs"]:
            if job.get("name") == "grok-daily-brief":
                job["delivery"] = {"mode": "none", "bestEffort": True}
                break
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            tmp_path = f.name
        try:
            proc = subprocess.run(
                [
                    "python3",
                    str(workspace / "tools" / "cron-jobs-tool.py"),
                    "validate",
                    tmp_path,
                ],
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("delivery.mode", proc.stderr)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_two_core_workflows_have_expected_schedules(self):
        workspace = Path(__file__).resolve().parents[1]
        jobs = {
            job["name"]: job["schedule"]["expr"]
            for job in load_core_jobs_fixture(workspace)
        }

        self.assertEqual(jobs["grok-daily-brief"], "0 8 * * *")
        self.assertEqual(jobs["alpha-polymarket"], "0 * * * *")
        self.assertNotIn("kimi-polymarket", jobs)


if __name__ == "__main__":
    unittest.main()

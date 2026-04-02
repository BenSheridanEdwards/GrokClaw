import json
import subprocess
import unittest
from pathlib import Path


def load_core_jobs_fixture(workspace: Path) -> list[dict]:
    fixture_path = workspace / "tests" / "fixtures" / "core-cron-jobs.json"
    return json.loads(fixture_path.read_text(encoding="utf-8")).get("jobs", [])


class WorkflowPromptTests(unittest.TestCase):
    def test_repo_cron_jobs_define_the_four_core_workflows(self):
        workspace = Path(__file__).resolve().parents[1]
        jobs = load_core_jobs_fixture(workspace)
        names = [job.get("name") for job in jobs]

        self.assertEqual(
            names,
            [
                "grok-daily-brief",
                "grok-openclaw-research",
                "alpha-polymarket",
                "kimi-polymarket",
            ],
        )

    def test_four_workflow_prompts_include_lifecycle_and_research_paths(self):
        workspace = Path(__file__).resolve().parents[1]
        jobs = {
            job["name"]: job
            for job in load_core_jobs_fixture(workspace)
        }

        daily_brief = jobs["grok-daily-brief"]["payload"]["message"]
        self.assertIn("./tools/cron-paperclip-lifecycle.sh start grok-daily-brief grok", daily_brief)
        self.assertIn("Paperclip issues from the last 24 hours", daily_brief)
        self.assertIn("audit log", daily_brief.lower())
        self.assertIn("data/linear-creations/", daily_brief)
        self.assertIn("user_request", daily_brief)
        self.assertIn("./tools/telegram-suggestion.sh", daily_brief)
        self.assertIn('PAPERCLIP_ISSUE_UUID=$(cat "$ISSUE_FILE") ./tools/cron-run-record.sh grok-daily-brief grok', daily_brief)

        openclaw = jobs["grok-openclaw-research"]["payload"]["message"]
        self.assertIn("./tools/cron-paperclip-lifecycle.sh start grok-openclaw-research grok", openclaw)
        self.assertIn("morning", openclaw.lower())
        self.assertIn("afternoon", openclaw.lower())
        self.assertIn("evening", openclaw.lower())
        self.assertIn("data/research/openclaw/", openclaw)

        alpha = jobs["alpha-polymarket"]["payload"]["message"]
        self.assertIn("./tools/cron-paperclip-lifecycle.sh start alpha-polymarket alpha", alpha)
        self.assertIn("data/alpha/research/", alpha)
        self.assertIn("./tools/agent-report.sh alpha alpha-polymarket", alpha)

        kimi = jobs["kimi-polymarket"]["payload"]["message"]
        self.assertIn("./tools/cron-paperclip-lifecycle.sh start kimi-polymarket kimi", kimi)
        self.assertIn("data/kimi/research/", kimi)
        self.assertIn("./tools/agent-report.sh kimi kimi-polymarket", kimi)

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

    def test_four_core_workflows_have_expected_schedules(self):
        workspace = Path(__file__).resolve().parents[1]
        jobs = {
            job["name"]: job["schedule"]["expr"]
            for job in load_core_jobs_fixture(workspace)
        }

        self.assertEqual(jobs["grok-daily-brief"], "0 8 * * *")
        self.assertEqual(jobs["grok-openclaw-research"], "0 7,13,19 * * *")
        self.assertEqual(jobs["alpha-polymarket"], "0 * * * *")
        self.assertEqual(jobs["kimi-polymarket"], "0 * * * *")

    def test_committed_cron_jobs_match_core_fixture(self):
        """cron/jobs.json must exist and stay aligned with the redacted fixture (workflow-health compares runtime to repo)."""
        workspace = Path(__file__).resolve().parents[1]
        repo_path = workspace / "cron" / "jobs.json"
        self.assertTrue(repo_path.is_file(), "cron/jobs.json is required for workflow-health scheduler checks")
        fixture_by_name = {j["name"]: j for j in load_core_jobs_fixture(workspace)}
        repo_data = json.loads(repo_path.read_text(encoding="utf-8"))
        repo_by_name = {j["name"]: j for j in repo_data.get("jobs", [])}
        self.assertEqual(set(repo_by_name.keys()), set(fixture_by_name.keys()))
        for name, fj in fixture_by_name.items():
            rj = repo_by_name[name]
            self.assertEqual(rj["schedule"], fj["schedule"])
            self.assertEqual(rj["payload"], fj["payload"])
            self.assertEqual(rj.get("agentId"), fj.get("agentId"))
            rd, fd = rj.get("delivery") or {}, fj.get("delivery") or {}
            self.assertEqual(rd.get("mode"), fd.get("mode"))
            self.assertEqual(rd.get("channel"), fd.get("channel"))
            self.assertEqual(rd.get("bestEffort"), fd.get("bestEffort"))
            # Repo uses a placeholder supergroup id; sync merges the real id from ~/.openclaw at deploy time.
            self.assertTrue(
                str(rd.get("to", "")).startswith("-100"),
                "delivery.to must look like a Telegram supergroup id",
            )
        tool = workspace / "tools" / "cron-jobs-tool.py"
        proc = subprocess.run(
            ["python3", str(tool), "validate", str(repo_path)],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout or "validate failed")


if __name__ == "__main__":
    unittest.main()

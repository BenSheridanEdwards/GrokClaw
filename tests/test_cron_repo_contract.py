"""Contract tests: checked-in cron/jobs.json vs workflow-health core set."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

AGENT_TURN_KINDS = frozenset({"agentTurn", "agent_turn"})


def _load_workflow_health_module(root: Path):
    path = root / "tools" / "_workflow_health.py"
    spec = importlib.util.spec_from_file_location("workflow_health_mod", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CronRepoContractTests(unittest.TestCase):
    def test_agentturn_job_names_match_core_workflows(self) -> None:
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / "cron" / "jobs.json").read_text(encoding="utf-8"))
        names = {
            j["name"]
            for j in data.get("jobs", [])
            if isinstance(j, dict)
            and isinstance(j.get("payload"), dict)
            and j.get("payload", {}).get("kind") in AGENT_TURN_KINDS
        }
        mod = _load_workflow_health_module(root)
        self.assertEqual(names, set(mod.CORE_WORKFLOWS.keys()))


    def test_all_agentturn_jobs_have_message_payload(self) -> None:
        """Every agentTurn job must have a non-empty message field.
        Without it, the agent starts with no instructions and silently fails."""
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / "cron" / "jobs.json").read_text(encoding="utf-8"))
        for job in data.get("jobs", []):
            if not isinstance(job, dict):
                continue
            payload = job.get("payload")
            if not isinstance(payload, dict):
                continue
            if payload.get("kind") not in AGENT_TURN_KINDS:
                continue
            name = job.get("name", "?")
            msg = (payload.get("message") or "").strip()
            self.assertTrue(
                msg,
                f"Job '{name}' has agentTurn payload but no 'message' field — "
                f"agent will start with no instructions",
            )

    def test_all_agentturn_jobs_reference_orchestrator(self) -> None:
        """Every agentTurn message must invoke cron-core-workflow-run.sh so the
        orchestrator handles lifecycle, locking, and evidence checks."""
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / "cron" / "jobs.json").read_text(encoding="utf-8"))
        for job in data.get("jobs", []):
            if not isinstance(job, dict):
                continue
            payload = job.get("payload")
            if not isinstance(payload, dict):
                continue
            if payload.get("kind") not in AGENT_TURN_KINDS:
                continue
            name = job.get("name", "?")
            msg = (payload.get("message") or "")
            self.assertIn(
                "cron-core-workflow-run.sh",
                msg,
                f"Job '{name}' message does not reference cron-core-workflow-run.sh",
            )


if __name__ == "__main__":
    unittest.main()

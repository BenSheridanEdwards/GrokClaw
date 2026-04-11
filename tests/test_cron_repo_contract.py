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


if __name__ == "__main__":
    unittest.main()

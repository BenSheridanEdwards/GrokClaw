import unittest
from pathlib import Path


class NorthStarDocTests(unittest.TestCase):
    def setUp(self):
        self.northstar = (
            Path(__file__).resolve().parents[1] / "NorthStar.md"
        ).read_text(encoding="utf-8")

    def test_northstar_describes_event_driven_workflow_health_architecture(self):
        self.assertIn("event-driven workflow validation at the end of each core run", self.northstar)
        self.assertIn("self-healing only for low-risk infrastructure failures", self.northstar)
        self.assertIn("doctor as the missed-run and drift catch-all", self.northstar)
        self.assertIn("approval-gated Linear remediation for workflow failures with code risk", self.northstar)

    def test_northstar_documents_cancelled_and_husky_gate(self):
        self.assertIn("`cancelled`", self.northstar)
        self.assertIn("Husky", self.northstar)
        self.assertIn("`tools/test-all.sh`", self.northstar)


if __name__ == "__main__":
    unittest.main()

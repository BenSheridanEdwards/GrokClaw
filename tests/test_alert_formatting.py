import importlib.util
import sys
import unittest
from pathlib import Path


def _load_health_module():
    repo = Path(__file__).resolve().parents[1]
    path = repo / "tools" / "_workflow_health.py"
    name = "grokclaw_workflow_health_fmt_test"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


wh = _load_health_module()

INTERNAL_KINDS = set(wh.HUMAN_LABELS.keys())


class AlertMessageFormattingTests(unittest.TestCase):
    """Ensure health alerts sent to Telegram are human-readable, not internal codes."""

    def test_single_failure_uses_human_label(self):
        failures = [{"workflow": "grok-daily-brief", "kind": "missing_audit", "message": "..."}]
        msg = wh.build_alert_message(failures)
        self.assertIn("no Telegram post found", msg)
        self.assertNotIn("missing_audit", msg)

    def test_multiple_failures_grouped_by_workflow(self):
        failures = [
            {"workflow": "alpha-polymarket", "kind": "missing_run", "message": "..."},
            {"workflow": "alpha-polymarket", "kind": "missing_research", "message": "..."},
            {"workflow": "grok-daily-brief", "kind": "error_run", "message": "..."},
        ]
        msg = wh.build_alert_message(failures)
        self.assertIn("alpha-polymarket: did not run, no research file written", msg)
        self.assertIn("grok-daily-brief: last run errored", msg)

    def test_no_internal_kind_names_in_alert(self):
        for kind in INTERNAL_KINDS:
            failures = [{"workflow": "grok-daily-brief", "kind": kind, "message": "test"}]
            msg = wh.build_alert_message(failures)
            self.assertNotIn(
                kind, msg,
                f"Internal kind '{kind}' leaked into alert: {msg!r}",
            )

    def test_alert_includes_remediation(self):
        failures = [{"workflow": "alpha-polymarket", "kind": "missing_run", "message": "..."}]
        msg = wh.build_alert_message(failures)
        self.assertIn("Rerun", msg)

    def test_healthy_message(self):
        msg = wh.build_alert_message([])
        self.assertEqual(msg, "Workflow health: all clear")

    def test_alert_under_telegram_limit(self):
        failures = [
            {"workflow": f"workflow-{i}", "kind": "missing_run", "message": "x" * 200}
            for i in range(10)
        ]
        msg = wh.build_alert_message(failures)
        self.assertLessEqual(len(msg), 4096, "Telegram messages must be under 4096 chars")

    def test_alert_has_blank_line_before_remediation(self):
        failures = [{"workflow": "grok-daily-brief", "kind": "stale_run", "message": "..."}]
        msg = wh.build_alert_message(failures)
        lines = msg.split("\n")
        self.assertTrue(
            any(line == "" for line in lines),
            f"Alert should have a blank line separating failures from fix:\n{msg}",
        )


class DraftFormattingTests(unittest.TestCase):
    """Ensure Linear drafts use human labels, not internal codes."""

    def test_draft_evidence_uses_human_labels(self):
        failures = [
            {"workflow": "alpha-polymarket", "kind": "missing_research", "message": "..."},
        ]
        draft = wh.build_draft(failures, "abc123")
        self.assertIn("no research file written", draft["description"])
        self.assertNotIn("missing_research", draft["description"])

    def test_draft_includes_remediation(self):
        failures = [
            {"workflow": "grok-daily-brief", "kind": "missing_run", "message": "..."},
        ]
        draft = wh.build_draft(failures, "abc123")
        self.assertIn("Suggested fixes", draft["description"])


class HumanLabelCoverageTests(unittest.TestCase):
    """Every remediation hint must have a corresponding human label."""

    def test_all_remediation_kinds_have_human_labels(self):
        for kind in wh.REMEDIATION_HINTS:
            self.assertIn(
                kind, wh.HUMAN_LABELS,
                f"REMEDIATION_HINTS has '{kind}' but HUMAN_LABELS does not",
            )

    def test_all_human_labels_have_remediation_hints(self):
        for kind in wh.HUMAN_LABELS:
            self.assertIn(
                kind, wh.REMEDIATION_HINTS,
                f"HUMAN_LABELS has '{kind}' but REMEDIATION_HINTS does not",
            )


if __name__ == "__main__":
    unittest.main()

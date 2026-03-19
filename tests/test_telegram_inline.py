"""Tests for Telegram inline button logic (_telegram_inline.py)."""
import json
import unittest
from pathlib import Path

# Import after adding workspace to path so we can load the module
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from _telegram_inline import (
    _action_to_label,
    action_token,
    build_keyboard,
    button_label,
)


class TelegramInlineButtonTests(unittest.TestCase):
    """Deterministic tests for button label and keyboard layout."""

    def test_button_label_uses_clean_text_only(self):
        """Button displays only text, never callback_data."""
        btn = {"text": "Approve", "callback_data": "approve_idea:12:GRO-21"}
        self.assertEqual(button_label(btn), "Approve")

    def test_button_label_fallback_from_action_prefix(self):
        """When text is empty, derive label from action prefix."""
        btn = {"text": "", "callback_data": "approve_idea:12:GRO-21"}
        self.assertEqual(button_label(btn), "Approve")

    def test_button_label_merge_reject_fallback(self):
        """Merge and reject actions get capitalized labels."""
        self.assertEqual(button_label({"callback_data": "merge:123:GRO-22"}), "Merge")
        self.assertEqual(button_label({"callback_data": "reject:123:GRO-22"}), "Reject")

    def test_action_token_from_callback_data(self):
        """Action token comes from callback_data."""
        btn = {"text": "Approve", "callback_data": "approve_idea:12:GRO-21"}
        self.assertEqual(action_token(btn), "approve_idea:12:GRO-21")

    def test_build_keyboard_compact_one_row(self):
        """All buttons in a single row for compact layout."""
        buttons = json.dumps([
            {"text": "Approve", "callback_data": "approve_idea:10:GRO-25"},
            {"text": "Reject", "callback_data": "reject:10:GRO-25"},
        ])
        kb = build_keyboard(buttons)
        self.assertEqual(len(kb), 1, "Should have one row")
        self.assertEqual(len(kb[0]), 2, "Row should have two buttons")

    def test_build_keyboard_hidden_callback_data(self):
        """Button text is clean label; callback_data not in display."""
        buttons = json.dumps([
            {"text": "Approve", "callback_data": "approve_idea:10:GRO-25"},
        ])
        kb = build_keyboard(buttons)
        btn = kb[0][0]
        self.assertEqual(btn["text"], "Approve")
        self.assertEqual(btn["switch_inline_query_current_chat"], "approve_idea:10:GRO-25")
        self.assertNotIn("approve_idea", btn["text"])
        self.assertNotIn("GRO-25", btn["text"])

    def test_build_keyboard_empty_returns_empty(self):
        """Empty or invalid button-json produces empty keyboard."""
        self.assertEqual(build_keyboard("[]"), [])
        self.assertEqual(build_keyboard('[{"text":"","callback_data":""}]'), [])

    def test_action_to_label_prefix_mapped(self):
        """Action prefix maps to clean label (approve_idea->Approve, merge->Merge)."""
        self.assertEqual(_action_to_label("approve_idea:12:GRO-21"), "Approve")
        self.assertEqual(_action_to_label("merge:1:GRO-1"), "Merge")
        self.assertEqual(_action_to_label("reject:2:GRO-2"), "Reject")

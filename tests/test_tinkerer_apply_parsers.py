"""Unit tests for tinkerer markdown parsers in tools/tinkerer-apply.py."""

import importlib.util
import sys
import unittest
from pathlib import Path


_tinkerer_apply_mod = None


def _load_tinkerer_apply():
    global _tinkerer_apply_mod
    if _tinkerer_apply_mod is not None:
        return _tinkerer_apply_mod
    workspace = Path(__file__).resolve().parents[1]
    path = workspace / "tools" / "tinkerer-apply.py"
    spec = importlib.util.spec_from_file_location("grokclaw_tinkerer_apply_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _tinkerer_apply_mod = module
    return module


class ParseSensitiveDataTests(unittest.TestCase):
    def test_extracts_contact_fields_from_example_shape(self):
        mod = _load_tinkerer_apply()
        text = """## Contact

- **Email**: a@b.co
- **Phone**: +1 555 000 0000
- **Location**: Here, There
"""
        self.assertEqual(
            mod.parse_sensitive_data(text),
            {"email": "a@b.co", "phone": "+1 555 000 0000", "location": "Here, There"},
        )

    def test_keys_are_lowercased(self):
        mod = _load_tinkerer_apply()
        text = "- **EMAIL**: x@y.z\n"
        self.assertEqual(mod.parse_sensitive_data(text), {"email": "x@y.z"})

    def test_skips_empty_values(self):
        mod = _load_tinkerer_apply()
        text = "- **Email**: \n- **Phone**: ok\n"
        self.assertEqual(mod.parse_sensitive_data(text), {"phone": "ok"})

    def test_ignores_non_list_lines(self):
        mod = _load_tinkerer_apply()
        text = "Email: plain\n- **Email**: e@mail.com\n"
        self.assertEqual(mod.parse_sensitive_data(text), {"email": "e@mail.com"})


class ExtractNameTests(unittest.TestCase):
    def test_standard_builder_identity_block(self):
        mod = _load_tinkerer_apply()
        text = """## Identity

- **Name**: Ada Lovelace
- **Location**: London
"""
        self.assertEqual(mod.extract_name(text), "Ada Lovelace")

    def test_name_key_is_case_insensitive(self):
        mod = _load_tinkerer_apply()
        text = "- **name**: Pat Smith\n"
        self.assertEqual(mod.extract_name(text), "Pat Smith")

    def test_returns_empty_when_missing(self):
        mod = _load_tinkerer_apply()
        self.assertEqual(mod.extract_name("## Hello\n\nNo name line."), "")

    def test_returns_empty_when_value_blank(self):
        mod = _load_tinkerer_apply()
        self.assertEqual(mod.extract_name("- **Name**: \n"), "")

    def test_first_name_line_wins(self):
        mod = _load_tinkerer_apply()
        text = "- **Name**: First\n- **Name**: Second\n"
        self.assertEqual(mod.extract_name(text), "First")


class ParseSafeTrialTests(unittest.TestCase):
    """Headers must match write_safe_trial() / parse_safe_trial() exactly — see tools/tinkerer-apply.py."""

    def test_parses_three_sections_from_write_safe_trial_shape(self):
        mod = _load_tinkerer_apply()
        md = """# Tinkerer Application — Safe Trial

Generated on 2026-04-15 12:00 UTC

## Form Fields

### Name
N

### Email Address
e@test

### Phone Number
p

### Location
loc

### GitHub / Projects
g

### Which challenge are you submitting?
c

### Submission
Line one of submission
Line two

### Where are you currently on your AI journey?
Journey para one

Journey para two

### What keeps you excited about the future?
Excite single line
"""
        out = mod.parse_safe_trial(md)
        self.assertEqual(
            out["submission"],
            "Line one of submission\nLine two",
        )
        self.assertEqual(
            out["ai_journey"],
            "Journey para one\n\nJourney para two",
        )
        self.assertEqual(out["excitement"], "Excite single line")

    def test_wrong_journey_header_does_not_split_sections(self):
        """If the journey header text drifts from the template, ai_journey stays empty; excitement still parses."""
        mod = _load_tinkerer_apply()
        md = """### Submission
Only sub

### Where are you on your AI journey?
Wrong header — missing 'currently'

### What keeps you excited about the future?
Excitement text
"""
        out = mod.parse_safe_trial(md)
        self.assertEqual(
            out["submission"],
            "Only sub\n\n### Where are you on your AI journey?\nWrong header — missing 'currently'",
        )
        self.assertEqual(out["ai_journey"], "")
        self.assertEqual(out["excitement"], "Excitement text")

    def test_double_space_in_submission_header_skips_submission_but_later_headers_still_work(self):
        """If ### Submission is typo'd (e.g. extra space), body lines are ignored until a recognized header."""
        mod = _load_tinkerer_apply()
        md = "###  Submission\nignored body\n### Where are you currently on your AI journey?\nJourney ok\n"
        out = mod.parse_safe_trial(md)
        self.assertEqual(out["submission"], "")
        self.assertEqual(out["ai_journey"], "Journey ok")
        self.assertEqual(out["excitement"], "")

    def test_no_recognized_headers_yields_empty_sections(self):
        mod = _load_tinkerer_apply()
        md = "## Some other doc\n\nNo ### Submission etc.\n"
        out = mod.parse_safe_trial(md)
        self.assertEqual(
            out,
            {"submission": "", "ai_journey": "", "excitement": ""},
        )


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_module():
    workspace = Path(__file__).resolve().parents[1]
    path = workspace / "tools" / "_telegram_post.py"
    spec = importlib.util.spec_from_file_location("grokclaw_telegram_post_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TelegramPostTests(unittest.TestCase):
    def test_main_uses_default_timeout(self):
        module = _load_module()
        response = type(
            "Response",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, exc_type, exc, tb: False,
                "read": lambda self: json.dumps({"ok": True, "result": {"message_id": 1}}).encode("utf-8"),
            },
        )()
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["timeout"] = timeout
            return response

        with patch("urllib.request.urlopen", fake_urlopen), patch("builtins.print"):
            exit_code = module.main(["token", "123", "4", "hello"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["timeout"], 10)

    def test_main_allows_timeout_override_from_env(self):
        module = _load_module()
        response = type(
            "Response",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, exc_type, exc, tb: False,
                "read": lambda self: json.dumps({"ok": True, "result": {"message_id": 1}}).encode("utf-8"),
            },
        )()
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["timeout"] = timeout
            return response

        with patch("urllib.request.urlopen", fake_urlopen), patch("builtins.print"), patch.dict(
            os.environ,
            {"TELEGRAM_API_TIMEOUT_SECONDS": "3"},
            clear=False,
        ):
            exit_code = module.main(["token", "123", "4", "hello"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["timeout"], 3)

    def test_main_truncates_message_over_telegram_limit(self):
        module = _load_module()
        long_text = "x" * 5000
        captured_body = {}

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps({"ok": True, "result": {"message_id": 2}}).encode("utf-8")

        def fake_urlopen(request, timeout=None):
            captured_body["raw"] = request.data
            return _Resp()

        with patch("urllib.request.urlopen", fake_urlopen), patch("builtins.print"):
            exit_code = module.main(["token", "123", "4", long_text])

        self.assertEqual(exit_code, 0)
        payload = json.loads(captured_body["raw"].decode())
        text = payload["text"]
        self.assertLessEqual(len(text), module.TELEGRAM_MAX_MESSAGE_LENGTH)
        self.assertIn(module.TRUNCATION_SUFFIX.strip(), text)


if __name__ == "__main__":
    unittest.main()

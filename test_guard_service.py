import unittest
from unittest.mock import patch

from guard_service import (
    GuardUnavailableError,
    UnsafeContentError,
    _parse_guard_decision,
    assert_safe,
)


class GuardianTests(unittest.TestCase):
    def test_parser_accepts_only_the_decision_word(self):
        self.assertTrue(_parse_guard_decision("No"))
        self.assertFalse(_parse_guard_decision("Yes"))
        with self.assertRaises(ValueError):
            _parse_guard_decision("probably safe")

    @patch("guard_service.ollama.chat")
    def test_unsafe_text_is_blocked(self, chat):
        chat.return_value = {"message": {"content": "UNSAFE"}}
        with self.assertRaises(UnsafeContentError):
            assert_safe("unsafe request", "input")

    @patch("guard_service.ollama.chat")
    def test_guardian_failure_is_not_silently_bypassed(self, chat):
        chat.side_effect = RuntimeError("model unavailable")
        with self.assertRaises(GuardUnavailableError):
            assert_safe("ordinary archive question", "input")


if __name__ == "__main__":
    unittest.main()

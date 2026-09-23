"""
test_logic_manager.py

Hand-written test cases for src/logic/logic_manager.py.

No AI API calls are made here — every ai_output is a fake dict
constructed by hand to exercise a specific branch of the logic layer.

Run with:
    pytest tests/test_logic_manager.py
or directly:
    python tests/test_logic_manager.py
"""

import os
import sys

# Allow running this file directly (python tests/test_logic_manager.py)
# without the package being installed.
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "src", "logic")
)

from logic_manager import is_ai_unavailable  # noqa: E402


def test_is_ai_unavailable_true_when_classification_matches():
    fake_ai_output = {
        "classification": "AI_UNAVAILABLE",
        "confidence": 0,
        "tactics_detected": [],
        "suspicious_urls": [],
        "suspicious_attachments": [],
        "sender_domain_mismatch": False,
    }

    assert is_ai_unavailable(fake_ai_output) is True


def test_is_ai_unavailable_false_for_normal_classification():
    fake_ai_output = {
        "classification": "phishing",
        "confidence": 92,
        "tactics_detected": ["executive_impersonation"],
        "suspicious_urls": ["http://bad-domain.example/login"],
        "suspicious_attachments": [],
        "sender_domain_mismatch": True,
    }

    assert is_ai_unavailable(fake_ai_output) is False


def test_is_ai_unavailable_false_when_classification_missing():
    fake_ai_output = {
        "confidence": 10,
        "tactics_detected": [],
    }

    assert is_ai_unavailable(fake_ai_output) is False


def test_is_ai_unavailable_false_for_malformed_input():
    # Not a dict at all — function should tolerate this and return
    # False rather than raising, since classify_severity() relies on
    # this as a safe first check.
    assert is_ai_unavailable(None) is False
    assert is_ai_unavailable("AI_UNAVAILABLE") is False
    assert is_ai_unavailable([]) is False


def _run_all_tests():
    tests = [
        test_is_ai_unavailable_true_when_classification_matches,
        test_is_ai_unavailable_false_for_normal_classification,
        test_is_ai_unavailable_false_when_classification_missing,
        test_is_ai_unavailable_false_for_malformed_input,
    ]
    for test in tests:
        test()
        print(f"PASSED: {test.__name__}")
    print(f"\n{len(tests)} test(s) passed.")


if __name__ == "__main__":
    _run_all_tests()

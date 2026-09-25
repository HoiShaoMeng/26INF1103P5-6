#ONLY FOR TESTING!
#hard coded test cases for logic_manager.py, every ai_output below is a fake dict, no AI API calls.
#to run, enter this in terminal: python3 tests/test_logic_manager.py

import os
import sys

#adds the src/logic folder to the path so we can import logic_manager.py for testing.
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "src", "logic")
)

from logic_manager import classify_severity, is_ai_unavailable  # type: ignore #pulls in the ACTUAL functions from logic_manager.py for testing. #the "type: ignore" is to silence a false positive IDE warning

#test case: a properly formed AI_UNAVAILABLE placeholder should be detected as unavailable
def test_is_ai_unavailable_true_when_classification_matches():
    fake_ai_output = {
        "classification": "AI_UNAVAILABLE",
        "threat_level": 0,
        "tactics_detected": [],
        "suspicious_urls": [],
        "suspicious_attachments": [],
        "sender_domain_mismatch": False,
    }
    assert is_ai_unavailable(fake_ai_output) is True

#test case: a normal successful AI response should NOT be flagged as unavailable
def test_is_ai_unavailable_false_for_normal_classification():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 92,
        "tactics_detected": ["executive_impersonation"],
        "suspicious_urls": ["http://bad-domain.example/login"],
        "suspicious_attachments": [],
        "sender_domain_mismatch": True,
    }
    assert is_ai_unavailable(fake_ai_output) is False

#test case: if classification key is missing entirely, should default safely to False, not crash
def test_is_ai_unavailable_false_when_classification_missing():
    fake_ai_output = {"threat_level": 10, "tactics_detected": []}
    assert is_ai_unavailable(fake_ai_output) is False

#test case: garbage input types (None, strings, a list) should default safely to False
def test_is_ai_unavailable_false_for_malformed_input():
    #Must not crash on bad input, classify_severity() relies on this as a safe first check.
    assert is_ai_unavailable(None) is False
    assert is_ai_unavailable("AI_UNAVAILABLE") is False
    assert is_ai_unavailable([]) is False

#test case: fail-safe must win even when other fields look critical
def test_classify_severity_ai_unavailable_returns_needs_review():
    fake_ai_output = {
        "classification": "AI_UNAVAILABLE",
        "threat_level": 95,
        "tactics_detected": ["executive_impersonation"],
        "suspicious_urls": [],
        "suspicious_attachments": [],
        "sender_domain_mismatch": True,
    }
    assert classify_severity(fake_ai_output) == "NEEDS_REVIEW"

#test case: threat_level 80+ alone is CRITICAL, no tactics needed
def test_classify_severity_critical_from_threat_level_alone():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 85,
        "tactics_detected": [],
        "suspicious_urls": [],
        "suspicious_attachments": [],
        "sender_domain_mismatch": False,
    }
    assert classify_severity(fake_ai_output) == "CRITICAL"

#test case: threat_level 50-79 alone is NEEDS_REVIEW
def test_classify_severity_needs_review_from_threat_level_alone():
    fake_ai_output = {
        "classification": "spam",
        "threat_level": 65,
        "tactics_detected": [],
        "suspicious_urls": [],
        "suspicious_attachments": [],
        "sender_domain_mismatch": False,
    }
    assert classify_severity(fake_ai_output) == "NEEDS_REVIEW"

#test case: threat_level below 50 alone is LOG_ONLY
def test_classify_severity_log_only_from_threat_level_alone():
    fake_ai_output = {
        "classification": "benign",
        "threat_level": 12,
        "tactics_detected": [],
        "suspicious_urls": [],
        "suspicious_attachments": [],
        "sender_domain_mismatch": False,
    }
    assert classify_severity(fake_ai_output) == "LOG_ONLY"

#test case: missing threat_level field entirely should default safely to 0, landing in LOG_ONLY
def test_classify_severity_missing_threat_level_defaults_safely():
    fake_ai_output = {"classification": "benign", "tactics_detected": []}
    assert classify_severity(fake_ai_output) == "LOG_ONLY"

#test case: rule A, domain mismatch + a suspicious url is CRITICAL outright, even with a low threat_level
def test_classify_severity_rule_a_critical_with_low_threat_level():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 20,
        "tactics_detected": [],
        "suspicious_urls": ["http://fake-bank-login.example/reset"],
        "suspicious_attachments": [],
        "sender_domain_mismatch": True,
    }
    assert classify_severity(fake_ai_output) == "CRITICAL"

#test case: rule A, domain mismatch alone with NO evidence should NOT trigger CRITICAL
def test_classify_severity_rule_a_no_trigger_without_evidence():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 20,
        "tactics_detected": [],
        "suspicious_urls": [],
        "suspicious_attachments": [],
        "sender_domain_mismatch": True,
    }
    assert classify_severity(fake_ai_output) == "LOG_ONLY"

#test case: rule A, evidence alone with NO domain mismatch should NOT trigger CRITICAL
def test_classify_severity_rule_a_no_trigger_without_domain_mismatch():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 20,
        "tactics_detected": [],
        "suspicious_urls": ["http://fake-bank-login.example/reset"],
        "suspicious_attachments": [],
        "sender_domain_mismatch": False,
    }
    assert classify_severity(fake_ai_output) == "LOG_ONLY"

#runs every test above in sequence and prints a pass/fail summary
def _run_all_tests():
    tests = [
        test_is_ai_unavailable_true_when_classification_matches,
        test_is_ai_unavailable_false_for_normal_classification,
        test_is_ai_unavailable_false_when_classification_missing,
        test_is_ai_unavailable_false_for_malformed_input,
        test_classify_severity_ai_unavailable_returns_needs_review,
        test_classify_severity_critical_from_threat_level_alone,
        test_classify_severity_needs_review_from_threat_level_alone,
        test_classify_severity_log_only_from_threat_level_alone,
        test_classify_severity_missing_threat_level_defaults_safely,
        test_classify_severity_rule_a_critical_with_low_threat_level,
        test_classify_severity_rule_a_no_trigger_without_evidence,
        test_classify_severity_rule_a_no_trigger_without_domain_mismatch,
    ]
    for test in tests:
        test()
        print(f"PASSED: {test.__name__}")
    print(f"{len(tests)} test(s) passed.")

#runs only when the file is executed directly (python3 tests/test_logic_manager.py)
if __name__ == "__main__":
    _run_all_tests()

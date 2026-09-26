#ONLY FOR TESTING!
#hard coded test cases for logic_manager.py, every ai_output below is a fake dict, no AI API calls.
#to run, enter this in terminal: python3 tests/test_logic_manager.py

import os
import sys

#adds the src/logic folder to the path so we can import logic_manager.py for testing.
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "src", "logic")
)

from logic_manager import (  # type: ignore
    check_campaign,
    classify_severity,
    is_ai_unavailable,
)

#test case: a properly formed AI_UNAVAILABLE placeholder should be detected as unavailable
def test_is_ai_unavailable_true_when_classification_matches():
    fake_ai_output = {
        "classification": "AI_UNAVAILABLE",
        "threat_level": 0,
        "tactics_detected": [],
    }
    assert is_ai_unavailable(fake_ai_output) is True

#test case: a normal successful AI response should NOT be flagged as unavailable
def test_is_ai_unavailable_false_for_normal_classification():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 92,
        "tactics_detected": ["executive_impersonation"],
    }
    assert is_ai_unavailable(fake_ai_output) is False

#test case: fail-safe must win even when other fields look critical
def test_classify_severity_ai_unavailable_returns_needs_review():
    fake_ai_output = {
        "classification": "AI_UNAVAILABLE",
        "threat_level": 95,
        "tactics_detected": ["executive_impersonation"],
        "sender_domain_mismatch": True,
    }
    assert classify_severity(fake_ai_output) == "NEEDS_REVIEW"

#test case: threat_level 80+ alone is CRITICAL, no tactics needed
def test_classify_severity_critical_from_threat_level_alone():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 85,
        "tactics_detected": [],
    }
    assert classify_severity(fake_ai_output) == "CRITICAL"

#test case: threat_level 50-79 alone is NEEDS_REVIEW
def test_classify_severity_needs_review_from_threat_level_alone():
    fake_ai_output = {
        "classification": "spam",
        "threat_level": 65,
        "tactics_detected": [],
    }
    assert classify_severity(fake_ai_output) == "NEEDS_REVIEW"

#test case: threat_level below 50 alone is LOG_ONLY
def test_classify_severity_log_only_from_threat_level_alone():
    fake_ai_output = {
        "classification": "benign",
        "threat_level": 12,
        "tactics_detected": [],
    }
    assert classify_severity(fake_ai_output) == "LOG_ONLY"

#test case: rule A, domain mismatch + a suspicious url is CRITICAL outright, even with a low threat_level
def test_classify_severity_rule_a_critical_with_low_threat_level():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 20,
        "tactics_detected": [],
        "suspicious_urls": ["http://fake-bank-login.example/reset"],
        "sender_domain_mismatch": True,
    }
    assert classify_severity(fake_ai_output) == "CRITICAL"

#test case: rule B, 2+ tactics detected escalates NEEDS_REVIEW up to CRITICAL
def test_classify_severity_rule_b_escalates_needs_review_to_critical():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 60,
        "tactics_detected": ["urgency_pressure", "lookalike_domain"],
    }
    assert classify_severity(fake_ai_output) == "CRITICAL"

#test case: rule C, is_campaign=True forces CRITICAL even with a very low threat_level and no other signals
def test_classify_severity_rule_c_campaign_forces_critical():
    fake_ai_output = {
        "classification": "spam",
        "threat_level": 5,
        "tactics_detected": [],
    }
    assert classify_severity(fake_ai_output, is_campaign=True) == "CRITICAL"

#test case: check_campaign, 3 reports (current + 2 previous) from the same sender within 24h -> True
def test_check_campaign_true_for_three_reports_same_sender():
    current_report = {"sender_email": "attacker@evil.com", "reported_at": "2026-09-23T10:00:00"}
    previous_reports = [
        {"sender_email": "attacker@evil.com", "reported_at": "2026-09-23T09:00:00"},
        {"sender_email": "attacker@evil.com", "reported_at": "2026-09-23T08:00:00"},
    ]
    assert check_campaign(current_report, previous_reports) is True

#test case: check_campaign, only 2 total reports (current + 1 previous) should NOT count as a campaign
def test_check_campaign_false_for_only_two_reports():
    current_report = {"sender_email": "attacker@evil.com", "reported_at": "2026-09-23T10:00:00"}
    previous_reports = [
        {"sender_email": "attacker@evil.com", "reported_at": "2026-09-23T09:00:00"},
    ]
    assert check_campaign(current_report, previous_reports) is False

#runs every test above in sequence and prints a pass/fail summary
def _run_all_tests():
    tests = [
        test_is_ai_unavailable_true_when_classification_matches,
        test_is_ai_unavailable_false_for_normal_classification,
        test_classify_severity_ai_unavailable_returns_needs_review,
        test_classify_severity_critical_from_threat_level_alone,
        test_classify_severity_needs_review_from_threat_level_alone,
        test_classify_severity_log_only_from_threat_level_alone,
        test_classify_severity_rule_a_critical_with_low_threat_level,
        test_classify_severity_rule_b_escalates_needs_review_to_critical,
        test_classify_severity_rule_c_campaign_forces_critical,
        test_check_campaign_true_for_three_reports_same_sender,
        test_check_campaign_false_for_only_two_reports,
    ]
    for test in tests:
        test()
        print(f"PASSED: {test.__name__}")
    print(f"{len(tests)} test(s) passed.")

#runs only when the file is executed directly (python3 tests/test_logic_manager.py)
if __name__ == "__main__":
    _run_all_tests()

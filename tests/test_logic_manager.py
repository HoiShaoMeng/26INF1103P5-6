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

#test case: if classification key is missing entirely, should default safely to False, not crash
def test_is_ai_unavailable_false_when_classification_missing():
    fake_ai_output = {"threat_level": 10, "tactics_detected": []}
    assert is_ai_unavailable(fake_ai_output) is False

#test case: garbage input types (None, strings, a list) should default safely to False
def test_is_ai_unavailable_false_for_malformed_input():
    assert is_ai_unavailable(None) is False
    assert is_ai_unavailable("AI_UNAVAILABLE") is False
    assert is_ai_unavailable([]) is False

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
        "sender_domain_mismatch": True,
    }
    assert classify_severity(fake_ai_output) == "CRITICAL"

#test case: rule A, domain mismatch alone with NO evidence should NOT trigger CRITICAL
def test_classify_severity_rule_a_no_trigger_without_evidence():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 20,
        "tactics_detected": [],
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
    }
    assert classify_severity(fake_ai_output) == "LOG_ONLY"

#test case: rule B, 2+ tactics detected escalates LOG_ONLY up to NEEDS_REVIEW
def test_classify_severity_rule_b_escalates_log_only_to_needs_review():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 30,
        "tactics_detected": ["urgency_pressure", "lookalike_domain"],
    }
    assert classify_severity(fake_ai_output) == "NEEDS_REVIEW"

#test case: rule B, 2+ tactics detected escalates NEEDS_REVIEW up to CRITICAL
def test_classify_severity_rule_b_escalates_needs_review_to_critical():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 60,
        "tactics_detected": ["urgency_pressure", "lookalike_domain"],
    }
    assert classify_severity(fake_ai_output) == "CRITICAL"

#test case: rule B, already CRITICAL from threat_level stays CRITICAL, does not go out of bounds
def test_classify_severity_rule_b_stays_critical_when_already_critical():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 90,
        "tactics_detected": ["urgency_pressure", "lookalike_domain"],
    }
    assert classify_severity(fake_ai_output) == "CRITICAL"

#test case: rule B, only 1 tactic detected should NOT escalate anything
def test_classify_severity_rule_b_no_escalation_with_only_one_tactic():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 30,
        "tactics_detected": ["urgency_pressure"],
    }
    assert classify_severity(fake_ai_output) == "LOG_ONLY"

#test case: rule A and rule B both apply at once, rule A already forces CRITICAL, result stays CRITICAL
def test_classify_severity_rule_a_and_rule_b_together():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 20,
        "tactics_detected": ["urgency_pressure", "lookalike_domain"],
        "suspicious_urls": ["http://fake-bank-login.example/reset"],
        "sender_domain_mismatch": True,
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

#test case: rule C, is_campaign defaults to False when not passed in, behaves exactly as before
def test_classify_severity_rule_c_defaults_to_false_when_not_passed():
    fake_ai_output = {
        "classification": "benign",
        "threat_level": 12,
        "tactics_detected": [],
    }
    assert classify_severity(fake_ai_output) == "LOG_ONLY"

#test case: fail-safe still wins even if is_campaign=True, AI unavailability is checked first
def test_classify_severity_fail_safe_still_wins_over_campaign():
    fake_ai_output = {
        "classification": "AI_UNAVAILABLE",
        "threat_level": 5,
        "tactics_detected": [],
    }
    assert classify_severity(fake_ai_output, is_campaign=True) == "NEEDS_REVIEW"

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

#test case: check_campaign, same domain but different mailbox still counts as a match
def test_check_campaign_true_for_same_domain_different_sender():
    current_report = {"sender_email": "attacker1@evil.com", "reported_at": "2026-09-23T10:00:00"}
    previous_reports = [
        {"sender_email": "attacker2@evil.com", "reported_at": "2026-09-23T09:00:00"},
        {"sender_email": "attacker3@evil.com", "reported_at": "2026-09-23T08:00:00"},
    ]
    assert check_campaign(current_report, previous_reports) is True

#test case: check_campaign, matching sender but outside the 24h window should NOT count
def test_check_campaign_false_when_outside_time_window():
    current_report = {"sender_email": "attacker@evil.com", "reported_at": "2026-09-23T10:00:00"}
    previous_reports = [
        {"sender_email": "attacker@evil.com", "reported_at": "2026-09-20T09:00:00"},
        {"sender_email": "attacker@evil.com", "reported_at": "2026-09-19T08:00:00"},
    ]
    assert check_campaign(current_report, previous_reports) is False

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
        test_classify_severity_rule_b_escalates_log_only_to_needs_review,
        test_classify_severity_rule_b_escalates_needs_review_to_critical,
        test_classify_severity_rule_b_stays_critical_when_already_critical,
        test_classify_severity_rule_b_no_escalation_with_only_one_tactic,
        test_classify_severity_rule_a_and_rule_b_together,
        test_classify_severity_rule_c_campaign_forces_critical,
        test_classify_severity_rule_c_defaults_to_false_when_not_passed,
        test_classify_severity_fail_safe_still_wins_over_campaign,
        test_check_campaign_true_for_three_reports_same_sender,
        test_check_campaign_false_for_only_two_reports,
        test_check_campaign_true_for_same_domain_different_sender,
        test_check_campaign_false_when_outside_time_window,
    ]
    for test in tests:
        test()
        print(f"PASSED: {test.__name__}")
    print(f"{len(tests)} test(s) passed.")

#runs only when the file is executed directly (python3 tests/test_logic_manager.py)
if __name__ == "__main__":
    _run_all_tests()

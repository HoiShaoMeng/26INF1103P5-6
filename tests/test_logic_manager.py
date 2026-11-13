# ONLY FOR TESTING!
# hard coded test cases for logic_manager.py and severity_rules.py, every ai_output below is a fake dict, no AI API calls.
# run every test:              python tests/test_logic_manager.py
# run only some tests:         python tests/test_logic_manager.py campaign
# (the word is matched against the test names, e.g. campaign, boundary, action, unavailable, rule_b, xyz)

import os
import sys

# adds the src/logic folder to the path so we can import logic_manager.py for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "logic"))

from logic_manager import (  # type: ignore
    ActionRecommender,
    CampaignDetector,
    SeverityClassifier,
)
from severity_rules import AiUnavailableRule  # type: ignore

campaign_detector = CampaignDetector()
action_recommender = ActionRecommender()
classifier = SeverityClassifier()
ai_unavailable_rule = AiUnavailableRule()

# compares what the code returned with what we expected, prints both so you can see it working, then asserts
def check(description, actual, expected):
    #Severity members are also strings, str() turns them into plain text so the output shows 'CRITICAL'
    if isinstance(actual, str):
        actual = str(actual)
    result = "ok  " if actual == expected else "FAIL"
    print(f"   {result} {description}: got {actual!r}, expected {expected!r}")
    assert actual == expected

# test case: a properly formed AI_UNAVAILABLE placeholder should be detected as unavailable
def test_is_ai_unavailable_true_when_classification_matches():
    fake_ai_output = {
        "classification": "AI_UNAVAILABLE",
        "threat_level": 0,
        "tactics_detected": [],
    }
    check("classification AI_UNAVAILABLE", ai_unavailable_rule.matches(fake_ai_output, False, ""), True)

# test case: a normal successful AI response should NOT be flagged as unavailable
def test_is_ai_unavailable_false_for_normal_classification():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 92,
        "tactics_detected": ["executive_impersonation"],
    }
    check("classification phishing", ai_unavailable_rule.matches(fake_ai_output, False, ""), False)

# test case: anything that is not a dict (e.g. None) must not crash the rule, it just returns False
def test_is_ai_unavailable_false_for_non_dict():
    check("None instead of a dict", ai_unavailable_rule.matches(None, False, ""), False)
    check("plain text instead of a dict", ai_unavailable_rule.matches("AI_UNAVAILABLE", False, ""), False)

# test case: fail-safe must win even when other fields look critical
def test_classify_severity_ai_unavailable_returns_needs_review():
    fake_ai_output = {
        "classification": "AI_UNAVAILABLE",
        "threat_level": 95,
        "tactics_detected": ["executive_impersonation"],
        "sender_domain_mismatch": True,
    }
    check(
        "AI_UNAVAILABLE with threat 95 and a mismatch",
        classifier.classify(fake_ai_output),
        "NEEDS_REVIEW",
    )

# test case: threat_level 80+ alone is CRITICAL, no tactics needed
def test_classify_severity_critical_from_threat_level_alone():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 85,
        "tactics_detected": [],
    }
    check("threat 85, no tactics", classifier.classify(fake_ai_output), "CRITICAL")

# test case: threat_level 50-79 alone is NEEDS_REVIEW
def test_classify_severity_needs_review_from_threat_level_alone():
    fake_ai_output = {
        "classification": "spam",
        "threat_level": 65,
        "tactics_detected": [],
    }
    check("threat 65, no tactics", classifier.classify(fake_ai_output), "NEEDS_REVIEW")

# test case: threat_level below 50 alone is LOG_ONLY
def test_classify_severity_log_only_from_threat_level_alone():
    fake_ai_output = {
        "classification": "benign",
        "threat_level": 12,
        "tactics_detected": [],
    }
    check("threat 12, no tactics", classifier.classify(fake_ai_output), "LOG_ONLY")

# test case: rule A, domain mismatch + a suspicious url is CRITICAL outright, even with a low threat_level
def test_classify_severity_rule_a_critical_with_low_threat_level():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 20,
        "tactics_detected": [],
        "suspicious_urls": ["http://fake-bank-login.example/reset"],
        "sender_domain_mismatch": True,
    }
    check(
        "threat 20 + domain mismatch + suspicious url",
        classifier.classify(fake_ai_output),
        "CRITICAL",
    )

# test case: rule B, 2+ tactics detected escalates NEEDS_REVIEW up to CRITICAL
def test_classify_severity_rule_b_escalates_needs_review_to_critical():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 60,
        "tactics_detected": ["urgency_pressure", "lookalike_domain"],
    }
    check("threat 60 + 2 tactics", classifier.classify(fake_ai_output), "CRITICAL")

# test case: rule C, is_campaign=True forces CRITICAL even with a very low threat_level and no other signals
def test_classify_severity_rule_c_campaign_forces_critical():
    fake_ai_output = {
        "classification": "spam",
        "threat_level": 5,
        "tactics_detected": [],
    }
    check(
        "threat 5 + is_campaign True",
        classifier.classify(fake_ai_output, is_campaign=True),
        "CRITICAL",
    )

# test case: check_campaign, 3 reports (current + 2 previous) from the same sender within 24h -> True
def test_check_campaign_true_for_three_reports_same_sender():
    current_report = {
        "sender_email": "attacker@evil.com",
        "reported_at": "2026-09-23T10:00:00",
    }
    previous_reports = [
        {"sender_email": "attacker@evil.com", "reported_at": "2026-09-23T09:00:00"},
        {"sender_email": "attacker@evil.com", "reported_at": "2026-09-23T08:00:00"},
    ]
    check(
        "3 reports, same sender, within 2 hours",
        campaign_detector.check_campaign(current_report, previous_reports),
        True,
    )

# test case: check_campaign, only 2 total reports (current + 1 previous) should NOT count as a campaign
def test_check_campaign_false_for_only_two_reports():
    current_report = {
        "sender_email": "attacker@evil.com",
        "reported_at": "2026-09-23T10:00:00",
    }
    previous_reports = [
        {"sender_email": "attacker@evil.com", "reported_at": "2026-09-23T09:00:00"},
    ]
    check(
        "only 2 reports, same sender",
        campaign_detector.check_campaign(current_report, previous_reports),
        False,
    )

# test case: boundary, exactly 80 is CRITICAL but 79 is only NEEDS_REVIEW
def test_classify_severity_threat_level_80_boundary():
    check(
        "threat 80",
        classifier.classify(
            {"classification": "phishing", "threat_level": 80, "tactics_detected": []}
        ),
        "CRITICAL",
    )
    check(
        "threat 79",
        classifier.classify(
            {"classification": "phishing", "threat_level": 79, "tactics_detected": []}
        ),
        "NEEDS_REVIEW",
    )

# test case: boundary, exactly 50 is NEEDS_REVIEW but 49 is only LOG_ONLY
def test_classify_severity_threat_level_50_boundary():
    check(
        "threat 50",
        classifier.classify(
            {"classification": "spam", "threat_level": 50, "tactics_detected": []}
        ),
        "NEEDS_REVIEW",
    )
    check(
        "threat 49",
        classifier.classify(
            {"classification": "spam", "threat_level": 49, "tactics_detected": []}
        ),
        "LOG_ONLY",
    )

# test case: a missing threat_level is treated as 0, so it never crashes and falls to LOG_ONLY
def test_classify_severity_missing_threat_level_is_log_only():
    fake_ai_output = {
        "classification": "benign",
        "tactics_detected": [],
    }
    check("no threat_level field", classifier.classify(fake_ai_output), "LOG_ONLY")

# test case: the full placeholder ai_manager returns on failure (threat_level 50) must still give NEEDS_REVIEW
def test_classify_severity_full_ai_unavailable_placeholder_returns_needs_review():
    fake_ai_output = {
        "classification": "AI_UNAVAILABLE",
        "threat_level": 50,
        "tactics_detected": [],
        "suspicious_urls": [],
        "suspicious_attachments": [],
        "sender_domain_mismatch": False,
    }
    check(
        "ai_manager's real failure placeholder",
        classifier.classify(fake_ai_output),
        "NEEDS_REVIEW",
    )

# test case: no AI output at all (None) must not crash the classifier, it is treated like a failed AI call
def test_classify_severity_non_dict_ai_output_returns_needs_review():
    check("None instead of an AI output", classifier.classify(None), "NEEDS_REVIEW")

# test case: each severity gets the action from the spec table
def test_generate_recommended_action_for_each_severity():
    check(
        "CRITICAL",
        action_recommender.generate_recommended_action("CRITICAL"),
        "Block sender domain and alert all users.",
    )
    check(
        "NEEDS_REVIEW",
        action_recommender.generate_recommended_action("NEEDS_REVIEW"),
        "Perform a manual check within 24 hours.",
    )
    check(
        "LOG_ONLY",
        action_recommender.generate_recommended_action("LOG_ONLY"),
        "Archive the report. No further action required.",
    )


def test_generate_recommended_action_unknown_severity_falls_back_to_manual_review():
    check(
        "unknown severity HIGH",
        action_recommender.generate_recommended_action("HIGH"),
        "Unknown severity. Manual review required.",
    )

# test case: check_campaign, different senders from the same domain still count as a campaign
def test_check_campaign_true_for_same_domain_different_senders():
    current_report = {
        "sender_email": "ceo@evil.com",
        "reported_at": "2026-09-23T10:00:00",
    }
    previous_reports = [
        {"sender_email": "hr@evil.com", "reported_at": "2026-09-23T09:00:00"},
        {"sender_email": "it@evil.com", "reported_at": "2026-09-23T08:00:00"},
    ]
    check(
        "ceo@, hr@, it@ at evil.com",
        campaign_detector.check_campaign(current_report, previous_reports),
        True,
    )

# test case: check_campaign, a report older than 24 hours is not counted
def test_check_campaign_ignores_reports_older_than_24_hours():
    current_report = {
        "sender_email": "attacker@evil.com",
        "reported_at": "2026-09-23T10:00:00",
    }
    previous_reports = [
        {"sender_email": "attacker@evil.com", "reported_at": "2026-09-23T09:00:00"},
        {"sender_email": "attacker@evil.com", "reported_at": "2026-09-21T09:00:00"},
    ]
    check(
        "3rd report is 2 days old",
        campaign_detector.check_campaign(current_report, previous_reports),
        False,
    )

# test case: check_campaign works with the UTC timestamps io_manager now saves, e.g. 2026-09-23T10:00:00+00:00
def test_check_campaign_works_with_utc_timestamps():
    current_report = {
        "sender_email": "attacker@evil.com",
        "reported_at": "2026-09-23T10:00:00+00:00",
    }
    previous_reports = [
        {
            "sender_email": "attacker@evil.com",
            "reported_at": "2026-09-23T09:00:00+00:00",
        },
        {
            "sender_email": "attacker@evil.com",
            "reported_at": "2026-09-23T08:00:00+00:00",
        },
    ]
    check(
        "3 reports with +00:00 timestamps",
        campaign_detector.check_campaign(current_report, previous_reports),
        True,
    )

def test_check_campaign_counts_report_exactly_24_hours_old():
    current_report = {
        "sender_email": "alerts@example.com",
        "reported_at": "2026-11-09T12:00:00+00:00",
    }
    previous_reports = [
        {"sender_email": "first@example.com", "reported_at": "2026-11-08T12:00:00+00:00"},
        {"sender_email": "second@example.com", "reported_at": "2026-11-09T11:00:00+00:00"},
    ]
    check(
        "a matching report exactly 24 hours old counts",
        campaign_detector.check_campaign(current_report, previous_reports),
        True,
    )

def test_check_campaign_ignores_future_report():
    current_report = {
        "sender_email": "alerts@example.com",
        "reported_at": "2026-11-09T12:00:00+00:00",
    }
    previous_reports = [
        {"sender_email": "first@example.com", "reported_at": "2026-11-09T11:00:00+00:00"},
        {"sender_email": "second@example.com", "reported_at": "2026-11-09T12:01:00+00:00"},
    ]
    check(
        "a matching report in the future does not count",
        campaign_detector.check_campaign(current_report, previous_reports),
        False,
    )

# stand-in blocklist for the classifier tests: only contains_sender() is needed, no file is read
class FakeBlocklist:
    def __init__(self, blocked_senders):
        self._blocked_senders = blocked_senders

    def contains_sender(self, sender_email):
        return sender_email in self._blocked_senders


blocking_classifier = SeverityClassifier(blocklist=FakeBlocklist({"ceo@evil.com"}))


# test case: new feature, a blocked sender is CRITICAL even with threat 0, and even when the AI is down
def test_classify_severity_blocked_sender_is_critical():
    check(
        "blocked sender, threat 0",
        blocking_classifier.classify({"classification": "benign", "threat_level": 0}, sender_email="ceo@evil.com"),
        "CRITICAL",
    )
    check(
        "blocked sender, AI unavailable",
        blocking_classifier.classify({"classification": "AI_UNAVAILABLE"}, sender_email="ceo@evil.com"),
        "CRITICAL",
    )
    check(
        "blocked sender, no AI output at all",
        blocking_classifier.classify(None, sender_email="ceo@evil.com"),
        "CRITICAL",
    )


# test case: new feature, a sender that is not blocked follows the normal rules
def test_classify_severity_unblocked_sender_uses_normal_rules():
    check(
        "unblocked sender, threat 12",
        blocking_classifier.classify({"classification": "benign", "threat_level": 12}, sender_email="hr@good.com"),
        "LOG_ONLY",
    )


# test case: new safety net, a flagged url with a low threat_level is NEEDS_REVIEW, never LOG_ONLY
def test_classify_severity_suspicious_evidence_is_never_log_only():
    fake_ai_output = {
        "classification": "benign",
        "threat_level": 10,
        "tactics_detected": [],
        "suspicious_urls": ["http://bit.ly/x"],
        "sender_domain_mismatch": False,
    }
    check("threat 10 + flagged url, no mismatch", classifier.classify(fake_ai_output), "NEEDS_REVIEW")


# test case: new safety net, the floor can still be escalated by rule B, and never lowers a higher band
def test_classify_severity_suspicious_evidence_works_with_other_rules():
    check(
        "threat 10 + flagged attachment + 2 tactics",
        classifier.classify({"threat_level": 10, "suspicious_attachments": ["a.exe"],
                             "tactics_detected": ["urgency_pressure", "impersonation"]}),
        "CRITICAL",
    )
    check(
        "threat 85 + flagged url",
        classifier.classify({"threat_level": 85, "suspicious_urls": ["http://x.com"]}),
        "CRITICAL",
    )


# test case: rule B, 2+ tactics also lift LOG_ONLY to NEEDS_REVIEW, and CRITICAL never goes past CRITICAL
def test_classify_severity_rule_b_escalates_each_band_once():
    two_tactics = ["impersonation", "urgency_pressure"]
    check("threat 10 + 2 tactics", classifier.classify({"threat_level": 10, "tactics_detected": two_tactics}),
          "NEEDS_REVIEW")
    check("threat 90 + 2 tactics", classifier.classify({"threat_level": 90, "tactics_detected": two_tactics}),
          "CRITICAL")


# test case: rule B, a single tactic is not enough to escalate
def test_classify_severity_rule_b_one_tactic_does_not_escalate():
    check("threat 60 + 1 tactic",
          classifier.classify({"threat_level": 60, "tactics_detected": ["impersonation"]}), "NEEDS_REVIEW")


# test case: rule B, the tactic count needed can be changed when the classifier is created
def test_classify_severity_rule_b_threshold_is_configurable():
    strict_classifier = SeverityClassifier(min_tactics=3)
    check("threat 60 + 2 tactics, needs 3",
          strict_classifier.classify({"threat_level": 60, "tactics_detected": ["a", "b"]}), "NEEDS_REVIEW")


ALL_TESTS = [
    test_is_ai_unavailable_true_when_classification_matches,
    test_is_ai_unavailable_false_for_normal_classification,
    test_is_ai_unavailable_false_for_non_dict,
    test_classify_severity_ai_unavailable_returns_needs_review,
    test_classify_severity_critical_from_threat_level_alone,
    test_classify_severity_needs_review_from_threat_level_alone,
    test_classify_severity_log_only_from_threat_level_alone,
    test_classify_severity_rule_a_critical_with_low_threat_level,
    test_classify_severity_rule_b_escalates_needs_review_to_critical,
    test_classify_severity_rule_b_escalates_each_band_once,
    test_classify_severity_rule_b_one_tactic_does_not_escalate,
    test_classify_severity_rule_b_threshold_is_configurable,
    test_classify_severity_rule_c_campaign_forces_critical,
    test_check_campaign_true_for_three_reports_same_sender,
    test_check_campaign_false_for_only_two_reports,
    test_classify_severity_threat_level_80_boundary,
    test_classify_severity_threat_level_50_boundary,
    test_classify_severity_missing_threat_level_is_log_only,
    test_classify_severity_full_ai_unavailable_placeholder_returns_needs_review,
    test_classify_severity_non_dict_ai_output_returns_needs_review,
    test_classify_severity_blocked_sender_is_critical,
    test_classify_severity_unblocked_sender_uses_normal_rules,
    test_classify_severity_suspicious_evidence_is_never_log_only,
    test_classify_severity_suspicious_evidence_works_with_other_rules,
    test_generate_recommended_action_for_each_severity,
    test_generate_recommended_action_unknown_severity_falls_back_to_manual_review,
    test_check_campaign_true_for_same_domain_different_senders,
    test_check_campaign_ignores_reports_older_than_24_hours,
    test_check_campaign_works_with_utc_timestamps,
    test_check_campaign_counts_report_exactly_24_hours_old,
    test_check_campaign_ignores_future_report,
]

# runs every test whose name contains name_filter ("" means all), keeps going after a failure, returns 1 if any failed
def _run_tests(name_filter):
    selected = [test for test in ALL_TESTS if name_filter in test.__name__]
    if not selected:
        print(f"No test name contains '{name_filter}'. Available tests:")
        for test in ALL_TESTS:
            print("  " + test.__name__)
        return 1

    failed = []
    for test in selected:
        print()
        print(test.__name__)
        try:
            test()
            print("   -> PASSED")
        except AssertionError:
            print("   -> FAILED")
            failed.append(test.__name__)

    print()
    print(f"{len(selected) - len(failed)} of {len(selected)} test(s) passed.")
    if failed:
        print("Failed: " + ", ".join(failed))
        return 1
    return 0

# runs only when the file is executed directly, e.g. python tests/test_logic_manager.py campaign
if __name__ == "__main__":
    name_filter = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit(_run_tests(name_filter))

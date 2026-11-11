"""Unit tests for ReviewService, the analyst review feature: fake reports only, no AI API or file."""

import os
import sys

import pytest

# adds the src folders to the path so we can import the classes for testing.
for layer in ("logic", "data", "domain"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", layer))

from analyst_review import ReviewDecision  # type: ignore
from blocklist import Blocklist  # type: ignore
from logic_manager import ActionRecommender  # type: ignore
from report_history import ReportHistory  # type: ignore
from review_service import ReviewService  # type: ignore
from screening_report import ScreeningReport  # type: ignore

REVIEWED_AT = "2026-11-11T03:00:00+00:00"


# builds a saved report with only the fields the review uses
def make_report(sender_email, severity, report_id):
    return ScreeningReport.from_dict({
        "report_id": report_id,
        "sender_email": sender_email,
        "reported_at": "2026-11-11T02:00:00+00:00",
        "classification": "benign",
        "threat_level": 10,
        "severity": severity,
        "is_campaign": False,
        "recommended_action": "Archive the report. No further action required.",
    })


@pytest.fixture
def blocklist():
    return Blocklist()


@pytest.fixture
def service(blocklist):
    return ReviewService(ActionRecommender(), blocklist)


# --- apply_review ---
def test_confirmed_phishing_makes_a_missed_report_critical(service, blocklist):
    report = make_report("ceo@evil.com", "LOG_ONLY", "r1")

    review = service.apply_review(report, ReviewDecision.CONFIRMED_PHISHING, "Shao", "fake login", REVIEWED_AT)

    assert report.severity == "CRITICAL"
    assert report.decision.recommended_action == "Block sender domain and alert all users."
    assert review.previous_severity == "LOG_ONLY"
    assert review.new_severity == "CRITICAL"
    assert review.blocked_entry == "evil.com"
    assert blocklist.contains_sender("anyone@evil.com") is True


def test_review_keeps_the_original_ai_result(service):
    report = make_report("ceo@evil.com", "LOG_ONLY", "r1")
    service.apply_review(report, ReviewDecision.CONFIRMED_PHISHING, "Shao", "fake login", REVIEWED_AT)
    assert report.to_dict()["classification"] == "benign"
    assert report.to_dict()["review"]["analyst"] == "Shao"


def test_confirmed_safe_archives_without_blocking(service, blocklist):
    report = make_report("newsletter@shop.com", "NEEDS_REVIEW", "r1")

    review = service.apply_review(report, ReviewDecision.CONFIRMED_SAFE, "Shao", "real newsletter", REVIEWED_AT)

    assert report.severity == "LOG_ONLY"
    assert review.blocked_entry == ""
    assert len(blocklist) == 0


def test_confirmed_phishing_from_public_mail_blocks_only_that_address(service, blocklist):
    report = make_report("scammer@gmail.com", "LOG_ONLY", "r1")
    service.apply_review(report, ReviewDecision.CONFIRMED_PHISHING, "Shao", "scam", REVIEWED_AT)
    assert blocklist.contains_sender("scammer@gmail.com") is True
    assert blocklist.contains_sender("friend@gmail.com") is False


def test_review_records_the_time_when_none_is_given(service):
    report = make_report("ceo@evil.com", "LOG_ONLY", "r1")
    review = service.apply_review(report, ReviewDecision.CONFIRMED_SAFE, "Shao", "ok")
    assert review.reviewed_at.startswith("20")


# --- flag_related ---
def test_flag_related_sends_archived_reports_from_the_same_domain_back_for_review(service):
    confirmed = make_report("ceo@evil.com", "LOG_ONLY", "r1")
    same_domain = make_report("hr@evil.com", "LOG_ONLY", "r2")
    other_domain = make_report("hr@good.com", "LOG_ONLY", "r3")
    already_critical = make_report("it@evil.com", "CRITICAL", "r4")
    history = ReportHistory([confirmed, same_domain, other_domain, already_critical])
    service.apply_review(confirmed, ReviewDecision.CONFIRMED_PHISHING, "Shao", "fake login", REVIEWED_AT)

    flagged = service.flag_related(confirmed, history)

    assert flagged == [same_domain]
    assert same_domain.severity == "NEEDS_REVIEW"
    assert same_domain.flagged_by == "r1"
    assert other_domain.severity == "LOG_ONLY"
    assert already_critical.severity == "CRITICAL"


def test_flag_related_skips_reports_an_analyst_already_reviewed(service):
    confirmed = make_report("ceo@evil.com", "LOG_ONLY", "r1")
    checked_safe = make_report("hr@evil.com", "LOG_ONLY", "r2")
    history = ReportHistory([confirmed, checked_safe])
    service.apply_review(checked_safe, ReviewDecision.CONFIRMED_SAFE, "Shao", "real email", REVIEWED_AT)
    service.apply_review(confirmed, ReviewDecision.CONFIRMED_PHISHING, "Shao", "fake login", REVIEWED_AT)

    assert service.flag_related(confirmed, history) == []


def test_flag_related_for_public_mail_only_matches_the_exact_address(service):
    confirmed = make_report("scammer@gmail.com", "LOG_ONLY", "r1")
    same_address = make_report("scammer@gmail.com", "LOG_ONLY", "r2")
    other_gmail_user = make_report("friend@gmail.com", "LOG_ONLY", "r3")
    history = ReportHistory([confirmed, same_address, other_gmail_user])

    assert service.flag_related(confirmed, history) == [same_address]


def test_flag_related_with_invalid_sender_flags_nothing(service):
    confirmed = make_report("not-an-email", "LOG_ONLY", "r1")
    history = ReportHistory([confirmed, make_report("not-an-email", "LOG_ONLY", "r2")])
    assert service.flag_related(confirmed, history) == []

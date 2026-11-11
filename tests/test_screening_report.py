"""Unit tests for ScreeningReport, TriageDecision and AnalystReview: fake records only, no AI API or file."""

import os
import sys

import pytest

# adds the src/domain folder to the path so we can import the domain classes for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "domain"))

from analyst_review import AnalystReview, ReviewDecision  # type: ignore
from attachment import Attachment  # type: ignore
from screening_report import ScreeningReport, TriageDecision  # type: ignore

RECORD = {
    "sender_email": "support@paypa1.com",
    "sender_name": "PayPal Support",
    "subject": "Urgent: verify account",
    "body": "Dear customer...",
    "urls": ["http://paypa1.com/verify"],
    "attachments": [{"filename": "invoice.pdf.exe", "extension": "exe"}],
    "reported_at": "2026-11-11T02:00:00+00:00",
}
AI_OUTPUT = {
    "classification": "phishing",
    "threat_level": 92,
    "tactics_detected": ["impersonation"],
    "suspicious_urls": ["http://paypa1.com/verify"],
    "suspicious_attachments": ["invoice.pdf.exe"],
    "sender_domain_mismatch": True,
}
DECISION = TriageDecision("CRITICAL", False, "Block sender domain and alert all users.")


def make_review():
    return AnalystReview(ReviewDecision.CONFIRMED_PHISHING, "Shao", "fake login page",
                         "2026-11-11T03:00:00+00:00", "LOG_ONLY", "CRITICAL", "paypa1.com")


# --- create ---
def test_create_builds_the_saved_record_with_all_fields():
    saved = ScreeningReport.create(RECORD, AI_OUTPUT, DECISION).to_dict()
    expected_keys = ["report_id", "sender_email", "sender_name", "subject", "body", "urls", "attachments",
                     "reported_at", "classification", "threat_level", "tactics_detected", "suspicious_urls",
                     "suspicious_attachments", "sender_domain_mismatch", "is_campaign", "severity",
                     "recommended_action", "review", "flagged_by"]
    assert list(saved) == expected_keys
    assert saved["severity"] == "CRITICAL"
    assert saved["threat_level"] == 92
    assert saved["attachments"] == [{"filename": "invoice.pdf.exe", "extension": "exe"}]
    assert saved["review"] is None


@pytest.mark.parametrize("bad_record", [None, {}, {"sender_email": "a@x.com"}, {"reported_at": "2026-11-11"}])
def test_create_rejects_records_missing_sender_or_time(bad_record):
    with pytest.raises(ValueError):
        ScreeningReport.create(bad_record, AI_OUTPUT, DECISION)


def test_create_with_no_ai_output_saves_empty_ai_fields():
    saved = ScreeningReport.create(RECORD, None, DECISION).to_dict()
    assert saved["classification"] is None
    assert saved["tactics_detected"] == []


def test_each_report_gets_a_different_id():
    first = ScreeningReport.create(RECORD, AI_OUTPUT, DECISION)
    second = ScreeningReport.create(RECORD, AI_OUTPUT, DECISION)
    assert first.report_id != second.report_id
    assert len(first.report_id) == 8


# --- composition: the report owns its parts ---
def test_report_builds_its_own_attachment_objects():
    report = ScreeningReport.create(RECORD, AI_OUTPUT, DECISION)
    assert all(isinstance(item, Attachment) for item in report.attachments)
    assert report.attachments[0].extension == "exe"


def test_ai_output_property_is_a_copy():
    report = ScreeningReport.create(RECORD, AI_OUTPUT, DECISION)
    report.ai_output["threat_level"] = 0
    assert report.threat_level == 92


# --- from_dict ---
def test_saved_report_loads_back_the_same():
    saved = ScreeningReport.create(RECORD, AI_OUTPUT, DECISION).to_dict()
    assert ScreeningReport.from_dict(saved).to_dict() == saved


def test_old_part_1_report_without_id_gets_one():
    old = {key: value for key, value in RECORD.items()} | AI_OUTPUT | {
        "is_campaign": False, "severity": "LOG_ONLY", "recommended_action": "Archive."}
    report = ScreeningReport.from_dict(old)
    assert report.report_id
    assert report.severity == "LOG_ONLY"
    assert report.review is None


def test_partly_broken_saved_report_does_not_crash():
    report = ScreeningReport.from_dict({"subject": "only a subject", "attachments": ["junk", {"no": "name"}]})
    assert report.sender_email == ""
    assert report.attachments == []
    assert report.severity == ""


def test_unknown_saved_review_decision_is_ignored():
    saved = ScreeningReport.create(RECORD, AI_OUTPUT, DECISION).to_dict()
    saved["review"] = {"decision": "MAYBE"}
    assert ScreeningReport.from_dict(saved).review is None


# --- apply_review and flag_for_recheck ---
def test_apply_review_changes_decision_but_keeps_original_ai_output():
    report = ScreeningReport.create(RECORD, AI_OUTPUT, TriageDecision("LOG_ONLY", False, "Archive."))
    report.apply_review(make_review(), TriageDecision("CRITICAL", False, "Block."))

    saved = report.to_dict()
    assert saved["severity"] == "CRITICAL"
    assert saved["classification"] == "phishing"
    assert saved["review"]["decision"] == "CONFIRMED_PHISHING"
    assert saved["review"]["previous_severity"] == "LOG_ONLY"
    assert ScreeningReport.from_dict(saved).review.analyst == "Shao"


def test_flag_for_recheck_records_which_report_caused_it():
    report = ScreeningReport.create(RECORD, AI_OUTPUT, TriageDecision("LOG_ONLY", False, "Archive."))
    report.flag_for_recheck(TriageDecision("NEEDS_REVIEW", False, "Check."), "abc12345")
    assert report.severity == "NEEDS_REVIEW"
    assert report.to_dict()["flagged_by"] == "abc12345"


def test_review_decision_must_be_known():
    with pytest.raises(ValueError):
        AnalystReview("MAYBE", "Shao", "x", "", "LOG_ONLY", "CRITICAL")

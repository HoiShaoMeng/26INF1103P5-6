"""Unit tests for ReportListView: printed lines are collected in a list, so nothing goes to the screen."""

import os
import sys

# adds the src/io folder to the path so we can import report_list_view.py and text_view.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "io"))

from report_list_view import ReportListView  # type: ignore
from text_view import TextView  # type: ignore

REPORT = {"report_id": "abc12345", "sender_email": "alerts@paypa1.com", "sender_name": "PayPal",
          "subject": "Blocked funds", "classification": "PHISHING", "threat_level": 92,
          "is_campaign": True, "recommended_action": "Block the sender",
          "reported_at": "2026-11-12T08:30:00+00:00"}


def test_empty_list_says_nothing_is_saved():
    lines = ReportListView().build_lines([], "NEEDS_REVIEW")
    assert " NEEDS REVIEW REPORTS" in lines
    assert " No NEEDS REVIEW reports saved yet." in lines


def test_title_shows_the_count():
    lines = ReportListView().build_lines([REPORT, REPORT], "CRITICAL")
    assert lines[1] == " CRITICAL REPORTS  (2 saved, highest threat first)"


def test_reports_are_numbered_with_time_and_id():
    text = "\n".join(ReportListView().build_lines([REPORT, REPORT], "CRITICAL"))
    assert " [1]  12 Nov 2026, 16:30 SGT   id abc12345" in text
    assert " [2]  " in text


def test_every_field_is_shown():
    text = "\n".join(ReportListView().build_lines([REPORT], "CRITICAL"))
    for expected in ["PayPal <alerts@paypa1.com>", "Blocked funds", "PHISHING", "92 / 100",
                     "Campaign:", "YES", "Block the sender"]:
        assert expected in text


def test_missing_fields_show_as_unknown():
    text = "\n".join(ReportListView().build_lines([{}], "LOG_ONLY"))
    assert "From:" in text and "unknown" in text


def test_review_and_recheck_appear_only_when_present():
    plain = "\n".join(ReportListView().build_lines([REPORT], "CRITICAL"))
    assert "Review:" not in plain and "Re check:" not in plain

    reviewed = dict(REPORT, review={"decision": "CONFIRMED_PHISHING", "analyst": "Shao"}, flagged_by="def67890")
    text = "\n".join(ReportListView().build_lines([reviewed], "CRITICAL"))
    assert "confirmed phishing by Shao" in text
    assert "related to confirmed phishing report def67890" in text


def test_timestamp_is_shown_in_singapore_time():
    assert ReportListView.format_timestamp("2026-10-12T13:00:49+00:00") == "12 Oct 2026, 21:00 SGT"


def test_bad_timestamp_falls_back_to_plain_text():
    assert ReportListView.format_timestamp(None) == "unknown"
    assert ReportListView.format_timestamp("yesterday") == "yesterday"


def test_show_prints_a_blank_line_then_the_list():
    lines = []
    view = ReportListView(lines.append)
    view.show([REPORT], "CRITICAL")
    assert lines[0] == ""
    assert lines[1:] == view.build_lines([REPORT], "CRITICAL")


def test_report_list_view_is_a_text_view():
    assert isinstance(ReportListView(), TextView)
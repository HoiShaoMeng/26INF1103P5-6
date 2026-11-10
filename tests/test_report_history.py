"""Unit tests for ReportHistory: every report below is a fake dict, so no file or AI API is used."""

import os
import sys

import pytest

# adds the src/data folder to the path so we can import report_history.py for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "data"))

from report_history import ReportHistory  # type: ignore


# builds a small fake saved report with only the fields the queries use
def make_report(subject, severity, threat_level):
    return {"subject": subject, "severity": severity, "threat_level": threat_level}

SAVED_REPORTS = [
    make_report("a", "CRITICAL", 85),
    make_report("b", "LOG_ONLY", 10),
    make_report("c", "CRITICAL", 95),
    make_report("d", "NEEDS_REVIEW", 60),
    make_report("e", "CRITICAL", 85),
]

# returns just the subjects, so the order of reports is easy to check
def subjects(history):
    return [report["subject"] for report in history.reports]

# --- creating a history ---
def test_history_keeps_saved_reports_in_order():
    history = ReportHistory(SAVED_REPORTS)
    assert len(history) == 5
    assert subjects(history) == ["a", "b", "c", "d", "e"]

@pytest.mark.parametrize("bad_input", [None, "not a list", 42, {}])
def test_history_from_non_list_is_empty(bad_input):
    assert len(ReportHistory(bad_input)) == 0

def test_history_skips_items_that_are_not_report_dicts():
    history = ReportHistory([make_report("a", "CRITICAL", 90), "junk", None, 5])
    assert subjects(history) == ["a"]

def test_reports_property_returns_a_copy():
    history = ReportHistory(SAVED_REPORTS)
    history.reports.append(make_report("x", "CRITICAL", 99))
    assert len(history) == 5

# --- filter_by_severity ---
def test_filter_keeps_only_matching_severity_in_saved_order():
    critical = ReportHistory(SAVED_REPORTS).filter_by_severity("CRITICAL")
    assert subjects(critical) == ["a", "c", "e"]

@pytest.mark.parametrize("typed", ["needs review", " needs_review ", "Needs Review"])
def test_filter_normalises_case_and_spaces(typed):
    assert subjects(ReportHistory(SAVED_REPORTS).filter_by_severity(typed)) == ["d"]

def test_filter_with_no_match_or_non_string_is_empty():
    history = ReportHistory(SAVED_REPORTS)
    assert len(history.filter_by_severity("UNKNOWN")) == 0
    assert len(history.filter_by_severity(None)) == 0

def test_filter_does_not_change_the_original_history():
    history = ReportHistory(SAVED_REPORTS)
    history.filter_by_severity("CRITICAL")
    assert len(history) == 5

# --- sort_by_threat_level ---
def test_sort_puts_highest_threat_first_and_keeps_ties_in_saved_order():
    ordered = ReportHistory(SAVED_REPORTS).sort_by_threat_level()
    assert subjects(ordered) == ["c", "a", "e", "d", "b"]

def test_sort_puts_missing_or_bad_threat_levels_last():
    history = ReportHistory([
        make_report("missing", "CRITICAL", None),
        make_report("text", "CRITICAL", "high"),
        make_report("low", "CRITICAL", 0),
        make_report("high", "CRITICAL", 90),
    ])
    assert subjects(history.sort_by_threat_level()) == ["high", "low", "missing", "text"]

def test_sort_does_not_change_the_original_history():
    history = ReportHistory(SAVED_REPORTS)
    history.sort_by_threat_level()
    assert subjects(history) == ["a", "b", "c", "d", "e"]

# --- filter and sort together, the same steps as menu option 2 ---
def test_filter_then_sort_gives_the_option_2_view():
    view = ReportHistory(SAVED_REPORTS).filter_by_severity("CRITICAL").sort_by_threat_level()
    assert subjects(view) == ["c", "a", "e"]

def test_empty_history_filters_and_sorts_to_empty():
    view = ReportHistory([]).filter_by_severity("CRITICAL").sort_by_threat_level()
    assert view.reports == []

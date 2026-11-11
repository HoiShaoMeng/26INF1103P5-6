"""Unit tests for ReportHistory: every report below is a fake ScreeningReport, so no file or AI API is used."""

import os
import sys

import pytest

# adds the src/data and src/domain folders to the path so we can import the classes for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "data"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "domain"))

from report_history import ReportHistory  # type: ignore
from screening_report import ScreeningReport, TriageDecision  # type: ignore


# builds a small fake saved report with only the fields the queries use
def make_report(subject, severity, threat_level):
    return ScreeningReport.from_dict({"subject": subject, "severity": severity, "threat_level": threat_level})


def make_saved_reports():
    return [
        make_report("a", "CRITICAL", 85),
        make_report("b", "LOG_ONLY", 10),
        make_report("c", "CRITICAL", 95),
        make_report("d", "NEEDS_REVIEW", 60),
        make_report("e", "CRITICAL", 85),
    ]


# returns just the subjects, so the order of reports is easy to check
def subjects(history):
    return [report.to_dict()["subject"] for report in history.reports]


# --- creating a history ---
def test_history_keeps_saved_reports_in_order():
    history = ReportHistory(make_saved_reports())
    assert len(history) == 5
    assert subjects(history) == ["a", "b", "c", "d", "e"]


@pytest.mark.parametrize("bad_input", [None, "not a list", 42, {}])
def test_history_from_non_list_is_empty(bad_input):
    assert len(ReportHistory(bad_input)) == 0
    assert len(ReportHistory.from_dicts(bad_input)) == 0


def test_history_skips_items_that_are_not_reports():
    history = ReportHistory([make_report("a", "CRITICAL", 90), "junk", None, 5, {"subject": "dict"}])
    assert subjects(history) == ["a"]


def test_from_dicts_loads_saved_reports_and_skips_junk():
    history = ReportHistory.from_dicts([{"subject": "a", "severity": "CRITICAL"}, "junk", 5])
    assert subjects(history) == ["a"]
    assert history.reports[0].severity == "CRITICAL"


def test_to_dicts_gives_the_saved_form_back():
    saved = [make_report("a", "CRITICAL", 90).to_dict()]
    assert ReportHistory.from_dicts(saved).to_dicts() == saved


def test_reports_property_returns_a_copy():
    history = ReportHistory(make_saved_reports())
    history.reports.append(make_report("x", "CRITICAL", 99))
    assert len(history) == 5


def test_add_puts_a_new_report_at_the_end_and_ignores_non_reports():
    history = ReportHistory(make_saved_reports())
    history.add(make_report("new", "LOG_ONLY", 5))
    history.add({"subject": "not a report"})
    assert subjects(history)[-1] == "new"
    assert len(history) == 6


# --- aggregation: a filtered history shares the same report objects ---
def test_filtered_history_holds_the_same_report_objects():
    history = ReportHistory(make_saved_reports())
    critical = history.filter_by_severity("CRITICAL")
    report = critical.reports[0]
    report.flag_for_recheck(TriageDecision("LOG_ONLY", False, "Archive."), "x")
    assert history.reports[0].severity == "LOG_ONLY"


# --- filter_by_severity ---
def test_filter_keeps_only_matching_severity_in_saved_order():
    critical = ReportHistory(make_saved_reports()).filter_by_severity("CRITICAL")
    assert subjects(critical) == ["a", "c", "e"]


@pytest.mark.parametrize("typed", ["needs review", " needs_review ", "Needs Review"])
def test_filter_normalises_case_and_spaces(typed):
    assert subjects(ReportHistory(make_saved_reports()).filter_by_severity(typed)) == ["d"]


def test_filter_with_no_match_or_non_string_is_empty():
    history = ReportHistory(make_saved_reports())
    assert len(history.filter_by_severity("UNKNOWN")) == 0
    assert len(history.filter_by_severity(None)) == 0


def test_filter_does_not_change_the_original_history():
    history = ReportHistory(make_saved_reports())
    history.filter_by_severity("CRITICAL")
    assert len(history) == 5


# --- sort_by_threat_level ---
def test_sort_puts_highest_threat_first_and_keeps_ties_in_saved_order():
    ordered = ReportHistory(make_saved_reports()).sort_by_threat_level()
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
    history = ReportHistory(make_saved_reports())
    history.sort_by_threat_level()
    assert subjects(history) == ["a", "b", "c", "d", "e"]


# --- filter and sort together, the same steps as menu option 2 ---
def test_filter_then_sort_gives_the_option_2_view():
    view = ReportHistory(make_saved_reports()).filter_by_severity("CRITICAL").sort_by_threat_level()
    assert subjects(view) == ["c", "a", "e"]


def test_empty_history_filters_and_sorts_to_empty():
    view = ReportHistory([]).filter_by_severity("CRITICAL").sort_by_threat_level()
    assert view.reports == []

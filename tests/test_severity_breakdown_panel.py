"""Unit tests for SeverityBreakdownPanel: fake saved reports only, no file."""

import os
import sys

# adds the src/logic folder to the path so we can import the panel and the Severity enum
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "logic"))

from dashboard_panel import DashboardPanel  # type: ignore
from severity_breakdown_panel import SeverityBreakdownPanel  # type: ignore


# builds fake saved reports with the given severities
def reports_with(*severities):
    return [{"severity": severity} for severity in severities]


def test_counts_each_severity_highest_first():
    result = SeverityBreakdownPanel().build(reports_with("CRITICAL", "LOG_ONLY", "CRITICAL", "NEEDS_REVIEW"))
    assert result.title == "Severity breakdown"
    assert result.rows == [("CRITICAL", "2 (50%)"), ("NEEDS_REVIEW", "1 (25%)"),
                           ("LOG_ONLY", "1 (25%)"), ("total", 4)]


def test_a_severity_with_no_reports_shows_zero():
    rows = dict(SeverityBreakdownPanel().build(reports_with("CRITICAL")).rows)
    assert rows["LOG_ONLY"] == "0 (0%)"


def test_missing_or_unknown_severity_is_counted_as_other():
    rows = dict(SeverityBreakdownPanel().build([{"severity": "CRITICAL"}, {}, {"severity": "HIGH"}]).rows)
    assert rows["other"] == "2 (67%)"
    assert rows["total"] == 3


def test_other_is_left_out_when_every_severity_is_known():
    rows = dict(SeverityBreakdownPanel().build(reports_with("CRITICAL", "LOG_ONLY")).rows)
    assert "other" not in rows


def test_no_reports_gives_the_empty_note():
    result = SeverityBreakdownPanel().build([])
    assert result.is_empty
    assert result.note == "No reports saved yet."


def test_is_a_dashboard_panel():
    assert isinstance(SeverityBreakdownPanel(), DashboardPanel)
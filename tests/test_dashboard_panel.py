"""Unit tests for DashboardPanel and PanelResult, using a small fake panel."""

import os
import sys

import pytest

# adds the src/logic folder to the path so we can import dashboard_panel.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "logic"))

from dashboard_panel import DashboardPanel, PanelResult  # type: ignore


# a fake panel that just counts the reports, so the base class can be tested on its own
class CountPanel(DashboardPanel):
    TITLE = "Count"

    def compute_rows(self, reports):
        return [("reports", len(reports))]


def test_panel_result_keeps_its_values():
    result = PanelResult("Count", [("reports", 2)], "a note")
    assert result.title == "Count"
    assert result.rows == [("reports", 2)]
    assert result.note == "a note"
    assert not result.is_empty


def test_panel_result_values_are_read_only():
    result = PanelResult("Count", [("reports", 2)])
    with pytest.raises(AttributeError):
        result.title = "Other"
    with pytest.raises(AttributeError):
        result.rows = []


def test_changing_the_returned_rows_does_not_change_the_result():
    result = PanelResult("Count", [("reports", 2)])
    result.rows.append(("extra", 1))
    assert result.rows == [("reports", 2)]


def test_build_gives_the_title_and_rows():
    result = CountPanel().build([{}, {}])
    assert result.title == "Count"
    assert result.rows == [("reports", 2)]


def test_no_reports_gives_an_empty_result_with_a_note():
    result = CountPanel().build([])
    assert result.is_empty
    assert result.note == "No reports saved yet."


def test_dashboard_panel_cannot_be_created_on_its_own():
    with pytest.raises(TypeError):
        DashboardPanel()


def test_a_panel_without_compute_rows_cannot_be_created():
    class BrokenPanel(DashboardPanel):
        TITLE = "Broken"

    with pytest.raises(TypeError):
        BrokenPanel()
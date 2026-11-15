import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "io"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "logic"))

from dashboard_panel import PanelResult  # type: ignore
from dashboard_view import DashboardView  # type: ignore
from text_view import TextView  # type: ignore

SEVERITY = PanelResult("Severity breakdown", [("CRITICAL", "2 (50%)"), ("total", 4)])
TACTICS = PanelResult("Top tactics", [("urgency_pressure", 3)])
EMPTY = PanelResult("Active campaigns", [], "No reports saved yet.")


def test_starts_with_the_dashboard_title():
    lines = DashboardView().build_lines([SEVERITY])
    assert lines[1] == " DASHBOARD"


def test_each_panel_has_its_title_and_rows():
    lines = DashboardView().build_lines([SEVERITY, TACTICS])
    assert " Severity breakdown" in lines
    assert "   Critical:         2 (50%)" in lines
    assert "   Urgency pressure: 3" in lines


def test_values_start_in_the_same_column_across_panels():
    lines = DashboardView().build_lines([SEVERITY, TACTICS])
    critical = next(line for line in lines if "Critical" in line)
    tactic = next(line for line in lines if "Urgency" in line)
    assert critical.index("2 (50%)") == tactic.index("3")


def test_an_empty_panel_shows_its_note():
    lines = DashboardView().build_lines([EMPTY])
    assert " Active campaigns" in lines
    assert "   No reports saved yet." in lines


def test_only_empty_panels_still_build():
    assert DashboardView().build_lines([EMPTY, EMPTY])[-1].startswith("=")


def test_show_prints_through_the_given_function():
    lines = []
    DashboardView(lines.append).show([SEVERITY])
    assert lines[0] == ""
    assert " DASHBOARD" in lines


def test_is_a_text_view():
    assert isinstance(DashboardView(), TextView)
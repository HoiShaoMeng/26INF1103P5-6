"""Unit tests for TacticsPanel: fake saved reports only, no AI call."""

import os
import sys

# adds the src/logic folder to the path to import tactics_panel.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "logic"))

from dashboard_panel import DashboardPanel  # type: ignore
from tactics_panel import TacticsPanel  # type: ignore


def reports_with(*tactic_lists):
    return [{"tactics_detected": tactics} for tactics in tactic_lists]


def test_most_common_tactic_comes_first():
    rows = TacticsPanel().build(reports_with(["urgency_pressure", "impersonation"],
                                             ["urgency_pressure"], ["credential_harvesting"])).rows
    assert rows[0] == ("urgency_pressure", "2 of 3 reports")


def test_ties_are_in_alphabetical_order():
    rows = TacticsPanel().build(reports_with(["urgency_pressure", "impersonation"])).rows
    assert [tactic for tactic, _ in rows] == ["impersonation", "urgency_pressure"]


def test_only_the_top_5_are_shown():
    tactics = ["a", "b", "c", "d", "e", "f"]
    rows = TacticsPanel().build(reports_with(tactics, tactics[:5])).rows
    assert len(rows) == 5
    assert "f" not in dict(rows)


def test_a_tactic_repeated_in_one_report_counts_once():
    rows = TacticsPanel().build(reports_with(["impersonation", "Impersonation ", "impersonation"])).rows
    assert rows == [("impersonation", "1 of 1 reports")]


def test_missing_or_bad_tactics_are_ignored():
    rows = TacticsPanel().build([{}, {"tactics_detected": None}, {"tactics_detected": [3, ""]}]).rows
    assert rows == [("tactics_detected", "none recorded")]


def test_no_reports_gives_the_empty_note():
    assert TacticsPanel().build([]).note == "No reports saved yet."


def test_is_a_dashboard_panel():
    assert isinstance(TacticsPanel(), DashboardPanel)
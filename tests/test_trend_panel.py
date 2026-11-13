"""Unit tests for TrendPanel: "today" is fixed, so the results never depend on the real date."""

import os
import sys
from datetime import UTC, datetime

# adds the src/logic folder to the path so we can import trend_panel.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "logic"))

from dashboard_panel import DashboardPanel  # type: ignore
from trend_panel import TrendPanel  # type: ignore

# 13 Nov 2026, 13:30 in Singapore
NOW = datetime(2026, 11, 13, 5, 30, tzinfo=UTC)


def make_panel():
    return TrendPanel(clock=lambda: NOW)


def reported_at(*times):
    return [{"reported_at": time} for time in times]


def test_shows_the_last_7_days_oldest_first():
    rows = make_panel().build(reported_at("2026-11-13T01:00:00+00:00")).rows
    assert [label for label, _ in rows] == ["2026-11-07", "2026-11-08", "2026-11-09", "2026-11-10",
                                            "2026-11-11", "2026-11-12", "2026-11-13", "total"]


def test_counts_reports_per_day_with_a_bar():
    rows = dict(make_panel().build(reported_at("2026-11-13T01:00:00+00:00", "2026-11-13T02:00:00+00:00",
                                               "2026-11-10T03:00:00+00:00")).rows)
    assert rows["2026-11-13"] == "2  ##"
    assert rows["2026-11-10"] == "1  #"
    assert rows["2026-11-12"] == "0"
    assert rows["total"] == 3


def test_days_follow_singapore_time():
    # 12 Nov 17:00 UTC is already 13 Nov 01:00 in Singapore.
    rows = dict(make_panel().build(reported_at("2026-11-12T17:00:00+00:00")).rows)
    assert rows["2026-11-13"] == "1  #"


def test_older_reports_and_bad_times_are_left_out():
    rows = dict(make_panel().build(reported_at("2026-11-01T01:00:00+00:00", None, "yesterday")).rows)
    assert rows["total"] == 0


def test_long_bars_are_shrunk_to_fit():
    rows = dict(make_panel().build(reported_at(*["2026-11-13T01:00:00+00:00"] * 40)).rows)
    assert rows["2026-11-13"] == "40  " + "#" * 20


def test_no_reports_gives_the_empty_note():
    assert make_panel().build([]).note == "No reports saved yet."


def test_is_a_dashboard_panel():
    assert isinstance(make_panel(), DashboardPanel)
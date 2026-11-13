"""Unit tests for AiAvailabilityPanel: fake saved reports only, no AI calls."""

import os
import sys

# adds the src/logic folder to the path so we can import ai_availability_panel.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "logic"))

from ai_availability_panel import AiAvailabilityPanel  # type: ignore
from dashboard_panel import DashboardPanel  # type: ignore

ANSWERED = {"classification": "phishing", "reported_at": "2026-11-13T01:00:00+00:00"}
FAILED_EARLY = {"classification": "AI_UNAVAILABLE", "reported_at": "2026-11-12T06:05:00+00:00"}
FAILED_LATE = {"classification": "AI_UNAVAILABLE", "reported_at": "2026-11-13T02:00:00+00:00"}


def test_counts_answered_and_unavailable():
    rows = dict(AiAvailabilityPanel("test-model").build([ANSWERED, ANSWERED, ANSWERED, FAILED_EARLY]).rows)
    assert rows["answered"] == "3 of 4 (75%)"
    assert rows["unavailable"] == "1 of 4 (25%)"


def test_shows_the_model_it_was_given():
    rows = dict(AiAvailabilityPanel("test-model").build([ANSWERED]).rows)
    assert rows["model"] == "test-model"


def test_model_is_unknown_when_not_given():
    rows = dict(AiAvailabilityPanel().build([ANSWERED]).rows)
    assert rows["model"] == "unknown"


def test_last_failure_is_the_latest_in_singapore_time():
    rows = dict(AiAvailabilityPanel().build([FAILED_LATE, ANSWERED, FAILED_EARLY]).rows)
    assert rows["last_failure"] == "13 Nov 2026, 10:00 SGT"


def test_last_failure_is_none_when_the_ai_never_failed():
    rows = dict(AiAvailabilityPanel().build([ANSWERED]).rows)
    assert rows["last_failure"] == "none"


def test_failure_with_a_bad_time_is_counted_but_time_unknown():
    rows = dict(AiAvailabilityPanel().build([{"classification": "AI_UNAVAILABLE", "reported_at": None}]).rows)
    assert rows["unavailable"] == "1 of 1 (100%)"
    assert rows["last_failure"] == "unknown"


def test_no_reports_gives_the_empty_note():
    assert AiAvailabilityPanel().build([]).note == "No reports saved yet."


def test_is_a_dashboard_panel():
    assert isinstance(AiAvailabilityPanel(), DashboardPanel)
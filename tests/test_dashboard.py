"""Unit tests for Dashboard: fake saved reports and a fixed clock, so no file or real time is needed."""

import os
import sys
from datetime import UTC, datetime

# adds the src/logic folder to the path so we can import dashboard.py and the panels
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "logic"))

from dashboard import Dashboard  # type: ignore
from dashboard_panel import DashboardPanel  # type: ignore

NOW = datetime(2026, 11, 14, 4, 0, tzinfo=UTC)
REPORTS = [{"severity": "CRITICAL", "classification": "phishing", "sender_email": "a@paypa1.com",
            "reported_at": "2026-11-14T03:00:00+00:00", "red_flags": ["urgent language"]}]


# a fake panel that just counts the reports, so the dashboard can be tested without the real panels
class CountPanel(DashboardPanel):
    TITLE = "Count"

    def compute_rows(self, reports):
        return [("reports", len(reports))]


def test_builds_one_result_per_panel_in_order():
    results = Dashboard([CountPanel(), CountPanel()]).build([{}, {}, {}])
    assert [result.rows for result in results] == [[("reports", 3)], [("reports", 3)]]


def test_standard_dashboard_has_the_five_panels_in_order():
    titles = [result.title for result in Dashboard.standard("test-model", lambda: NOW).build(REPORTS)]
    assert titles == ["Severity breakdown", "Last 7 days", "Active campaigns", "Top tactics", "AI availability"]


def test_model_name_reaches_the_ai_panel():
    ai_result = Dashboard.standard("test-model", lambda: NOW).build(REPORTS)[-1]
    assert dict(ai_result.rows)["model"] == "test-model"


def test_no_reports_gives_every_panel_its_empty_note():
    results = Dashboard.standard(clock=lambda: NOW).build([])
    assert all(result.is_empty and result.note for result in results)


def test_changing_the_given_list_does_not_change_the_dashboard():
    panels = [CountPanel()]
    dashboard = Dashboard(panels)
    panels.append(CountPanel())
    assert len(dashboard.build([{}])) == 1
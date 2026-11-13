"""Unit tests for CampaignPanel: "now" is fixed, so the results never depend on the real time."""

import os
import sys
from datetime import UTC, datetime

# adds the src/logic folder to the path so we can import campaign_panel.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "logic"))

from campaign_panel import CampaignPanel  # type: ignore
from dashboard_panel import DashboardPanel  # type: ignore

# 13 Nov 2026, 20:30 in Singapore
NOW = datetime(2026, 11, 13, 12, 30, tzinfo=UTC)


def make_panel():
    return CampaignPanel(clock=lambda: NOW)


def report(sender, time):
    return {"sender_email": sender, "reported_at": time}


PAYPAL = [report("alerts@paypa1.com", "2026-11-13T10:00:00+00:00"),
          report("help@paypa1.com", "2026-11-13T11:00:00+00:00"),
          report("ALERTS@PAYPA1.COM", "2026-11-13T12:15:00+00:00")]


def test_three_reports_from_one_domain_is_a_campaign():
    rows = make_panel().build(PAYPAL).rows
    assert rows == [("campaign_1", "paypa1.com: 3 reports, latest 13 Nov 2026, 20:15 SGT")]


def test_two_reports_is_not_a_campaign():
    rows = make_panel().build(PAYPAL[:2]).rows
    assert rows == [("active_campaigns", "none in the last 24 hours")]


def test_reports_older_than_24_hours_are_not_active():
    old = [report("a@dhl-parcel.net", "2026-11-11T10:00:00+00:00")] * 3
    rows = dict(make_panel().build(old).rows)
    assert rows == {"active_campaigns": "none in the last 24 hours"}


def test_busiest_campaign_comes_first():
    dhl = [report("x@dhl-parcel.net", "2026-11-13T09:00:00+00:00")] * 4
    rows = make_panel().build(PAYPAL + dhl).rows
    assert rows[0][1].startswith("dhl-parcel.net: 4 reports")
    assert rows[1][1].startswith("paypa1.com: 3 reports")


def test_bad_senders_and_times_are_skipped():
    bad = [report(None, "2026-11-13T10:00:00+00:00"), report("not-an-email", "2026-11-13T10:00:00+00:00"),
           report("a@paypa1.com", "yesterday")]
    rows = make_panel().build(PAYPAL[:2] + bad).rows
    assert rows == [("active_campaigns", "none in the last 24 hours")]


def test_no_reports_gives_the_empty_note():
    assert make_panel().build([]).note == "No reports saved yet."


def test_is_a_dashboard_panel():
    assert isinstance(make_panel(), DashboardPanel)
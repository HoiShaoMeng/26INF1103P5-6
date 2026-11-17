"""End-to-end tests of App and TriageService: the real app with a fake AI client and a temp data folder.

Covers every menu option, AI failures and retries, corrupt files, save failures and leaving the app.
"""

import io
import json
import os
import runpy
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
for layer in ("io", "ai", "logic", "data", "domain"):
    sys.path.insert(0, os.path.join(ROOT, "src", layer))
sys.path.insert(0, ROOT)

from ai_manager import AIManager  # type: ignore
from data_manager import DataManager  # type: ignore
from exceptions import AIConnectionError  # type: ignore
from io_manager import IOManager  # type: ignore
from json_blocklist_store import JsonBlocklistStore  # type: ignore
from json_report_repository import JsonReportRepository  # type: ignore
from logic_manager import ActionRecommender  # type: ignore
from mock_ai_client import MockAIClient
from prompt_config import PromptConfig  # type: ignore

from app import App  # type: ignore
from triage_service import TriageService  # type: ignore

PHISHING = json.dumps({
    "classification": "phishing", "threat_level": 85, "tactics_detected": [],
    "suspicious_urls": [], "suspicious_attachments": [], "sender_domain_mismatch": False,
})


# the fake client also reports a model name, which the dashboard's AI availability panel shows
class ModelMockClient(MockAIClient):
    @property
    def model(self):
        return "test-model:free"


# a report store whose save always fails, e.g. a full disk
class FailingSaveRepository(JsonReportRepository):
    def save_all(self, reports):
        return False


# a blocklist store whose save always fails
class FailingSaveBlocklistStore(JsonBlocklistStore):
    def save(self, blocklist):
        return False


# one email typed into menu option 1 (menu: 1 screen, 2 view, 3 review, 4 dashboard, 5 exit)
def screen(sender="a@evil.com", subject="Reset password"):
    return ["1", sender, "", subject, "click here", "END", "n", "n"]


def build(tmp_path, ai_replies, data=None):
    data = data or DataManager.for_project(tmp_path)
    ai = AIManager(PromptConfig.load_from_yaml_file(), ModelMockClient(ai_replies))
    return data, ai


def run_app(tmp_path, answers, ai_replies=(), data=None):
    data, ai = build(tmp_path, list(ai_replies), data)
    typed = iter(answers + ["5"])
    io = IOManager(read_input=lambda prompt="": next(typed))
    recommender = ActionRecommender()
    triage = TriageService(ai, data, io, recommender)
    App(triage, data, recommender, io, "test-model:free").run()
    return data, ai, triage


def subjects_by_severity(data):
    return {report.to_dict()["subject"]: report.severity for report in data.load_history().reports}


# --- option 1: AI failures and retries ---
def test_ai_error_every_time_retries_three_times_then_needs_review(tmp_path, capsys):
    errors = [AIConnectionError("Rate limit hit (429)")] * 4
    data, ai, _ = run_app(tmp_path, screen(), errors)
    out = capsys.readouterr().out

    assert len(ai.client.calls) == 4
    assert "Retrying AI request (3/3)" in out
    assert "the AI could not give a valid assessment" in out
    assert subjects_by_severity(data) == {"Reset password": "NEEDS_REVIEW"}


def test_ai_fails_once_then_works_uses_the_second_answer(tmp_path):
    data, ai, _ = run_app(tmp_path, screen(), ["not json", PHISHING])
    assert len(ai.client.calls) == 2
    assert subjects_by_severity(data) == {"Reset password": "CRITICAL"}


def test_ai_answers_first_time_is_not_retried(tmp_path):
    _, ai, _ = run_app(tmp_path, screen(), [PHISHING])
    assert len(ai.client.calls) == 1


# --- option 1: saving ---
def test_save_failure_still_shows_the_result_and_an_error(tmp_path, capsys):
    failing = DataManager(FailingSaveRepository(tmp_path / "reports.json"),
                          JsonBlocklistStore(tmp_path / "blocklist.json"))
    run_app(tmp_path, screen(), [PHISHING], data=failing)
    out = capsys.readouterr().out
    assert "SCREENING RESULT" in out
    assert "the report could not be saved" in out


def test_screen_email_loads_data_itself_and_rejects_a_record_without_a_time(tmp_path):
    data, ai = build(tmp_path, [PHISHING])
    io = IOManager(read_input=lambda prompt="": "")
    triage = TriageService(ai, data, io, ActionRecommender())

    record = {"sender_email": "a@evil.com", "sender_name": "", "subject": "x", "body": "y",
              "urls": [], "attachments": []}
    assert triage.screen_email(record) is None
    assert triage.was_saved() is False
    assert len(data.load_history()) == 0


# --- option 2: view by severity ---
def test_view_lists_matching_reports_highest_threat_first(tmp_path, capsys):
    saved = [
        {"report_id": "low", "subject": "low", "severity": "CRITICAL", "threat_level": 60},
        {"report_id": "high", "subject": "high", "severity": "CRITICAL", "threat_level": 95},
        {"report_id": "other", "subject": "other", "severity": "LOG_ONLY", "threat_level": 99},
    ]
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "reports.json").write_text(json.dumps(saved), encoding="utf-8")

    run_app(tmp_path, ["2", "1"])
    out = capsys.readouterr().out
    assert out.index("high") < out.index("low")
    assert "Subject:        other" not in out


# --- option 3: review edge cases ---
def test_review_of_an_empty_list_returns_to_the_menu(tmp_path, capsys):
    run_app(tmp_path, ["3", "1"])
    assert "No CRITICAL reports saved yet" in capsys.readouterr().out


def test_cancelled_review_changes_nothing(tmp_path):
    #screen one LOG_ONLY email, then open it in option 3 and choose Cancel (3)
    benign = json.dumps({**json.loads(PHISHING), "classification": "benign", "threat_level": 10})
    data, _, _ = run_app(tmp_path, screen() + ["3", "3", "1", "3"], [benign])
    report = data.load_history().reports[0]
    assert report.severity == "LOG_ONLY"
    assert report.review is None
    assert len(data.load_blocklist()) == 0


def test_confirmed_safe_review_archives_without_blocking(tmp_path):
    data, _, _ = run_app(tmp_path, screen() + ["3", "1", "1", "2", "Shao", "real newsletter"], [PHISHING])
    report = data.load_history().reports[0]
    assert report.severity == "LOG_ONLY"
    assert report.review.decision == "CONFIRMED_SAFE"
    assert len(data.load_blocklist()) == 0


def test_review_save_failure_is_reported(tmp_path, capsys):
    #a saved CRITICAL report exists, but saving the review fails
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "reports.json").write_text(json.dumps(
        [{"report_id": "r1", "sender_email": "a@evil.com", "subject": "s", "severity": "CRITICAL",
          "threat_level": 90, "reported_at": "2026-11-15T01:00:00+00:00"}]), encoding="utf-8")
    failing = DataManager(FailingSaveRepository(tmp_path / "data" / "reports.json"),
                          JsonBlocklistStore(tmp_path / "data" / "blocklist.json"))
    run_app(tmp_path, ["3", "1", "1", "1", "Shao", "fake"], data=failing)
    assert "the review could not be saved" in capsys.readouterr().out


def test_blocklist_save_failure_is_reported(tmp_path, capsys):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "reports.json").write_text(json.dumps(
        [{"report_id": "r1", "sender_email": "a@evil.com", "subject": "s", "severity": "CRITICAL",
          "threat_level": 90, "reported_at": "2026-11-15T01:00:00+00:00"}]), encoding="utf-8")
    failing = DataManager(JsonReportRepository(tmp_path / "data" / "reports.json"),
                          FailingSaveBlocklistStore(tmp_path / "data" / "blocklist.json"))
    run_app(tmp_path, ["3", "1", "1", "1", "Shao", "fake"], data=failing)
    assert "the blocklist could not be saved" in capsys.readouterr().out


# --- option 4: dashboard ---
def test_dashboard_shows_every_panel_and_the_model(tmp_path, capsys):
    run_app(tmp_path, screen() + ["4"], [PHISHING])
    out = capsys.readouterr().out
    for heading in ("Severity breakdown", "Active campaigns", "Top tactics", "AI availability"):
        assert heading in out
    assert "test-model:free" in out


# --- corrupt data files never crash and are never overwritten ---
@pytest.mark.parametrize("answers", [["1"], ["2", "1"], ["3"], ["4"]])
def test_corrupt_reports_file_shows_an_error_on_every_option(tmp_path, capsys, answers):
    (tmp_path / "data").mkdir()
    reports = tmp_path / "data" / "reports.json"
    reports.write_text("{broken", encoding="utf-8")

    run_app(tmp_path, answers)

    assert "Data error: Reports file contains invalid JSON." in capsys.readouterr().out
    assert reports.read_text(encoding="utf-8") == "{broken"


def test_corrupt_blocklist_stops_screening(tmp_path, capsys):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "blocklist.json").write_text("[broken", encoding="utf-8")
    run_app(tmp_path, ["1"])
    assert "Data error: Blocklist file contains invalid JSON." in capsys.readouterr().out


# --- leaving the app ---
@pytest.mark.parametrize("error", [KeyboardInterrupt, EOFError])
def test_ctrl_c_or_end_of_input_exits_cleanly(tmp_path, capsys, error):
    data, ai = build(tmp_path, [])

    def stop(prompt=""):
        raise error

    io = IOManager(read_input=stop)
    recommender = ActionRecommender()
    App(TriageService(ai, data, io, recommender), data, recommender, io).run()
    assert "Exiting." in capsys.readouterr().out


def test_main_builds_the_app_and_exits_from_the_menu(monkeypatch, capsys):
    #runs main.py itself: no API key is needed to start, and typing 5 exits without touching data
    monkeypatch.setattr("sys.stdin", io.StringIO("5\n"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    runpy.run_path(os.path.join(ROOT, "main.py"), run_name="__main__")
    out = capsys.readouterr().out
    assert "Phishing Triage Assistant" in out
    assert "Exiting." in out

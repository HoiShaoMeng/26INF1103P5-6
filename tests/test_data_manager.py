"""Unit tests for DataManager and JsonBlocklistStore: uses pytest's tmp_path, never the real data/ folder."""

import json
import os
import sys

import pytest

# adds the src/data and src/domain folders to the path so we can import the classes for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "data"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "domain"))

from blocklist import Blocklist  # type: ignore
from data_manager import DataManager  # type: ignore
from json_blocklist_store import JsonBlocklistStore  # type: ignore
from json_report_repository import ReportStorageError  # type: ignore
from screening_report import ScreeningReport, TriageDecision  # type: ignore


# a fake storage that keeps reports in memory, so DataManager can be tested without real files
class InMemoryReportRepository:
    def __init__(self, reports=None):
        self.saved = list(reports or [])

    def load_all(self) -> list:
        return list(self.saved)

    def save_all(self, reports: list) -> bool:
        self.saved = list(reports)
        return True


def make_report(subject):
    record = {"sender_email": "a@x.com", "reported_at": "2026-11-11T02:00:00+00:00", "subject": subject}
    return ScreeningReport.create(record, {"threat_level": 40}, TriageDecision("LOG_ONLY", False, "Archive."))


# --- DataManager with the JSON files ---
def test_new_project_starts_with_empty_history_and_blocklist(tmp_path):
    data = DataManager.for_project(tmp_path)
    assert len(data.load_history()) == 0
    assert len(data.load_blocklist()) == 0


def test_history_saved_in_one_run_loads_in_the_next(tmp_path):
    history = DataManager.for_project(tmp_path).load_history()
    history.add(make_report("first"))
    assert DataManager.for_project(tmp_path).save_history(history) is True

    loaded = DataManager.for_project(tmp_path).load_history()
    assert [report.to_dict()["subject"] for report in loaded.reports] == ["first"]
    assert loaded.reports[0].report_id == history.reports[0].report_id


def test_corrupt_reports_file_raises_storage_error(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "reports.json").write_text("{broken", encoding="utf-8")
    with pytest.raises(ReportStorageError):
        DataManager.for_project(tmp_path).load_history()


def test_blocklist_saved_in_one_run_loads_in_the_next(tmp_path):
    blocklist = Blocklist()
    blocklist.block_sender("ceo@evil.com")
    assert DataManager.for_project(tmp_path).save_blocklist(blocklist) is True

    loaded = DataManager.for_project(tmp_path).load_blocklist()
    assert loaded.contains_sender("hr@evil.com") is True


# --- the storage is passed in, so a fake one can be used ---
def test_data_manager_works_with_a_fake_storage(tmp_path):
    repository = InMemoryReportRepository()
    data = DataManager(repository, JsonBlocklistStore(tmp_path / "blocklist.json"))

    history = data.load_history()
    history.add(make_report("in memory"))
    data.save_history(history)

    assert repository.saved[0]["subject"] == "in memory"


# --- JsonBlocklistStore failure cases ---
@pytest.mark.parametrize("contents", ["[broken", '{"evil.com": true}'])
def test_corrupt_blocklist_raises_storage_error_and_is_not_overwritten(tmp_path, contents):
    path = tmp_path / "blocklist.json"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ReportStorageError):
        JsonBlocklistStore(path).load()
    assert path.read_text(encoding="utf-8") == contents


def test_blocklist_file_is_a_sorted_json_list(tmp_path):
    path = tmp_path / "blocklist.json"
    JsonBlocklistStore(path).save(Blocklist(["z.com", "a.com"]))
    assert json.loads(path.read_text(encoding="utf-8")) == ["a.com", "z.com"]

import json
import os
import sys

import pytest

# adds the src/data folder to the path so we can import the repository for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "data"))

from json_report_repository import (  # type: ignore
    JsonReportRepository,
    ReportStorageError,
)


def test_load_all_returns_saved_reports(tmp_path):
    report_path = tmp_path / "reports.json"
    reports = [
        {"sender_email": "alerts@example.com", "severity": "NEEDS_REVIEW"},
        {"sender_email": "notice@example.com", "severity": "LOG_ONLY"},
    ]
    report_path.write_text(json.dumps(reports), encoding="utf-8")

    repository = JsonReportRepository(report_path)

    assert repository.load_all() == reports


def test_load_all_returns_empty_list_for_empty_history(tmp_path):
    report_path = tmp_path / "reports.json"
    report_path.write_text("[]", encoding="utf-8")

    repository = JsonReportRepository(report_path)

    assert repository.load_all() == []

def test_load_all_returns_empty_list_when_file_is_missing(tmp_path):
    report_path = tmp_path / "reports.json"

    assert JsonReportRepository(report_path).load_all() == []
    assert not report_path.exists()


@pytest.mark.parametrize("contents", ["{", '{"reports": []}'])
def test_load_all_rejects_corrupt_history(tmp_path, contents):
    report_path = tmp_path / "reports.json"
    report_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ReportStorageError):
        JsonReportRepository(report_path).load_all()

    assert report_path.read_text(encoding="utf-8") == contents


# --- save_all ---
def test_save_all_then_load_all_gives_the_same_reports(tmp_path):
    repository = JsonReportRepository(tmp_path / "reports.json")
    reports = [{"sender_email": "a@x.com", "severity": "CRITICAL", "subject": "café"}]

    assert repository.save_all(reports) is True
    assert repository.load_all() == reports


def test_save_all_creates_the_data_folder(tmp_path):
    repository = JsonReportRepository(tmp_path / "new_folder" / "reports.json")
    assert repository.save_all([]) is True
    assert (tmp_path / "new_folder" / "reports.json").exists()


def test_save_all_rejects_non_list(tmp_path):
    report_path = tmp_path / "reports.json"
    assert JsonReportRepository(report_path).save_all({"not": "a list"}) is False
    assert not report_path.exists()


def test_save_failure_keeps_old_file_and_removes_temp_file(tmp_path):
    report_path = tmp_path / "reports.json"
    report_path.write_text('[{"subject": "old"}]', encoding="utf-8")

    #a set cannot be written as JSON, so the save fails half way
    saved = JsonReportRepository(report_path).save_all([{"subject": "new", "bad": {1, 2}}])

    assert saved is False
    assert report_path.read_text(encoding="utf-8") == '[{"subject": "old"}]'
    assert not (tmp_path / "reports.json.tmp").exists()


def test_save_fails_cleanly_when_folder_cannot_be_created(tmp_path):
    #a plain file where the data folder should be means the folder cannot be created
    blocker = tmp_path / "data"
    blocker.write_text("not a folder", encoding="utf-8")

    assert JsonReportRepository(blocker / "reports.json").save_all([]) is False

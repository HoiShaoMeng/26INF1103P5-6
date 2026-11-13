"""Unit tests for JsonListFile: every case uses pytest's tmp_path, never the real data/ folder."""

import json
import os
import sys

import pytest

# adds the src/data folder to the path so we can import json_list_file.py for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "data"))

from json_list_file import JsonListFile, ReportStorageError  # type: ignore


# --- read ---
def test_missing_file_reads_as_empty_list(tmp_path):
    assert JsonListFile(tmp_path / "data.json", "Reports").read() == []


def test_saved_list_reads_back(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('[{"subject": "a"}]', encoding="utf-8")
    assert JsonListFile(path, "Reports").read() == [{"subject": "a"}]


@pytest.mark.parametrize("contents, problem", [
    ("{broken", "contains invalid JSON"),
    ('{"not": "a list"}', "must contain a list"),
])
def test_corrupt_file_raises_with_the_file_label(tmp_path, contents, problem):
    path = tmp_path / "data.json"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ReportStorageError, match=f"Blocklist file {problem}"):
        JsonListFile(path, "Blocklist").read()
    #the corrupt file is never changed, so nothing saved is lost
    assert path.read_text(encoding="utf-8") == contents


def test_file_that_is_not_utf8_raises(tmp_path):
    path = tmp_path / "data.json"
    path.write_bytes(b"\xff\xfe\x00broken")
    with pytest.raises(ReportStorageError, match="invalid JSON"):
        JsonListFile(path, "Reports").read()


def test_unreadable_path_raises(tmp_path):
    #a folder where the file should be cannot be opened as a file
    folder = tmp_path / "data.json"
    folder.mkdir()
    with pytest.raises(ReportStorageError, match="could not be read"):
        JsonListFile(folder, "Reports").read()


# --- write ---
def test_write_then_read_gives_the_same_list(tmp_path):
    data_file = JsonListFile(tmp_path / "data.json", "Reports")
    assert data_file.write([{"subject": "café"}]) is True
    assert data_file.read() == [{"subject": "café"}]


def test_write_creates_the_folder(tmp_path):
    assert JsonListFile(tmp_path / "new" / "data.json", "Reports").write([]) is True
    assert json.loads((tmp_path / "new" / "data.json").read_text(encoding="utf-8")) == []


def test_failed_write_keeps_old_file_and_removes_temp_file(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('["old"]', encoding="utf-8")

    #a set cannot be written as JSON, so the save fails half way
    assert JsonListFile(path, "Reports").write([{1, 2}]) is False

    assert path.read_text(encoding="utf-8") == '["old"]'
    assert not (tmp_path / "data.json.tmp").exists()


def test_write_fails_cleanly_when_folder_cannot_be_created(tmp_path):
    blocker = tmp_path / "data"
    blocker.write_text("not a folder", encoding="utf-8")
    assert JsonListFile(blocker / "data.json", "Reports").write([]) is False

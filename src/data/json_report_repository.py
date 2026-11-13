from pathlib import Path

#ReportStorageError is imported here too, so code that already imports it from this file keeps working
from json_list_file import JsonListFile, ReportStorageError  # noqa: F401


class JsonReportRepository:
    """Load and save reports in data/reports.json."""

    def __init__(self, file_path: Path):
        self._file = JsonListFile(file_path, "Reports")

    #every saved report as a dict, [] if nothing is saved yet, ReportStorageError if the file is corrupt
    def load_all(self) -> list:
        return self._file.read()

    #saves the whole report list, load_all() only accepts a list so never write anything else
    def save_all(self, reports: list) -> bool:
        if not isinstance(reports, list):
            return False
        return self._file.write(reports)

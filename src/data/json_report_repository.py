import json
from pathlib import Path


class JsonReportRepository:
    """Load saved reports from a JSON file."""

    def __init__(self, file_path: Path):
        self._file_path = file_path

    def load_all(self) -> list:
        try:
            with self._file_path.open("r", encoding="utf-8") as report_file:
                return json.load(report_file)
        except FileNotFoundError:
            return []
import json
from pathlib import Path


class ReportStorageError(Exception):
    """Raised when saved report history cannot be loaded."""


class JsonReportRepository:
    """Load saved reports from a JSON file."""

    def __init__(self, file_path: Path):
        self._file_path = file_path

    def load_all(self) -> list:
        try:
            with self._file_path.open("r", encoding="utf-8") as report_file:
                reports = json.load(report_file)
        except FileNotFoundError:
            return []
        except (json.JSONDecodeError, UnicodeError) as error:
            raise ReportStorageError("Reports file contains invalid JSON.") from error
        except OSError as error:
            raise ReportStorageError("Reports file could not be read.") from error

        if not isinstance(reports, list):
            raise ReportStorageError("Reports file must contain a list.")

        return reports
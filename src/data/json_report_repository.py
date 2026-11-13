import json
from pathlib import Path

from atomic_json_writer import AtomicJsonWriter


class ReportStorageError(Exception):
    """Raised when saved report history cannot be loaded."""


class JsonReportRepository:
    """Load and save reports in a JSON file."""

    def __init__(self, file_path: Path):
        self._file_path = Path(file_path)
        #the safe-write steps live in AtomicJsonWriter so they are not copied into every store that saves JSON
        self._writer = AtomicJsonWriter()

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

    #saves the whole report list, load_all() only accepts a list so never write anything else
    def save_all(self, reports: list) -> bool:
        if not isinstance(reports, list):
            return False
        return self._writer.write(self._file_path, reports)

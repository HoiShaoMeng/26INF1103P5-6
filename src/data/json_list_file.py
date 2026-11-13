"""json_list_file: one JSON file on disk that holds a list, read and written safely."""

import json
import os
from pathlib import Path


class ReportStorageError(Exception):
    """Raised when saved data cannot be loaded."""


#both data files (reports.json and blocklist.json) are a JSON list, so reading, error handling and
#the safe save live here once instead of being copied into each store.
class JsonListFile:

    def __init__(self, file_path: Path, label: str):
        self._file_path = Path(file_path)
        #used in error messages, e.g. "Reports" or "Blocklist"
        self._label = label

    #a missing file means nothing is saved yet, so it gives [].
    #a corrupt or unreadable file raises ReportStorageError instead of silently losing the saved data.
    def read(self) -> list:
        try:
            with self._file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return []
        except (json.JSONDecodeError, UnicodeError) as error:
            raise ReportStorageError(f"{self._label} file contains invalid JSON.") from error
        except OSError as error:
            raise ReportStorageError(f"{self._label} file could not be read.") from error

        if not isinstance(data, list):
            raise ReportStorageError(f"{self._label} file must contain a list.")
        return data

    #writes to a temp file first and only swaps it in once complete, so a crash half way never damages
    #the file already on disk. True if written, False if it failed (no print here, io shows the message).
    def write(self, data: list) -> bool:
        temp_path = self._file_path.with_name(self._file_path.name + ".tmp")
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            os.replace(temp_path, self._file_path)
            return True
        except (OSError, TypeError, ValueError):
            #OSError: no permission, disk full, folder cant be created. TypeError/ValueError: data cant be JSON
            self._remove_temp_file(temp_path)
            return False

    #deletes the half written temp file, errors are ignored because the save has already failed
    @staticmethod
    def _remove_temp_file(temp_path: Path) -> None:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass

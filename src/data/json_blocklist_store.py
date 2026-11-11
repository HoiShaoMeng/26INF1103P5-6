"""json_blocklist_store: saves and loads the blocklist in data/blocklist.json."""

import json
from pathlib import Path

from atomic_json_writer import AtomicJsonWriter
from blocklist import Blocklist
from json_report_repository import ReportStorageError


#reads and writes the blocklist as a JSON list of entries, e.g. ["evil.com", "scammer@gmail.com"]
class JsonBlocklistStore:

    def __init__(self, file_path: Path):
        self._file_path = Path(file_path)
        #composition: the store creates and owns its writer
        self._writer = AtomicJsonWriter()

    #missing file means nothing is blocked yet, a corrupt file is reported instead of silently unblocking everyone
    def load(self) -> Blocklist:
        try:
            with self._file_path.open("r", encoding="utf-8") as blocklist_file:
                entries = json.load(blocklist_file)
        except FileNotFoundError:
            return Blocklist()
        except (json.JSONDecodeError, UnicodeError) as error:
            raise ReportStorageError("Blocklist file contains invalid JSON.") from error
        except OSError as error:
            raise ReportStorageError("Blocklist file could not be read.") from error

        if not isinstance(entries, list):
            raise ReportStorageError("Blocklist file must contain a list.")

        return Blocklist(entries)

    #True if the blocklist was saved, False if it failed (old file left untouched)
    def save(self, blocklist: Blocklist) -> bool:
        return self._writer.write(self._file_path, blocklist.entries)

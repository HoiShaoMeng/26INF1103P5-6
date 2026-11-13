"""json_blocklist_store: saves and loads the blocklist in data/blocklist.json."""

from pathlib import Path

from blocklist import Blocklist
from json_list_file import JsonListFile


#the blocklist is saved as a JSON list of entries, e.g. ["evil.com", "scammer@gmail.com"]
class JsonBlocklistStore:

    def __init__(self, file_path: Path):
        self._file = JsonListFile(file_path, "Blocklist")

    #missing file means nothing is blocked yet, a corrupt file is reported instead of silently unblocking everyone
    def load(self) -> Blocklist:
        return Blocklist(self._file.read())

    #True if the blocklist was saved, False if it failed (old file left untouched)
    def save(self, blocklist: Blocklist) -> bool:
        return self._file.write(blocklist.entries)

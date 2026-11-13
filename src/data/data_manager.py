"""data_manager: the Data Manager, the one place the rest of the app goes to load and save data."""

from pathlib import Path

from json_blocklist_store import JsonBlocklistStore
from json_report_repository import JsonReportRepository
from report_history import ReportHistory
from report_repository import ReportRepository


#loads and saves the report history and the blocklist. it never prints, errors go back to the caller.
#dependency injection: the constructor accepts any ReportRepository, so storage can be swapped
#(e.g. an in-memory repository in tests or a database later) without changing this class.
#for_project() builds the default JSON parts that the running app uses.
class DataManager:

    def __init__(self, report_repository: ReportRepository, blocklist_store: JsonBlocklistStore):
        self._report_repository = report_repository
        self._blocklist_store = blocklist_store

    #builds the normal JSON setup inside the project's data/ folder (the Docker volume)
    @classmethod
    def for_project(cls, project_dir) -> "DataManager":
        data_dir = Path(project_dir) / "data"
        return cls(JsonReportRepository(data_dir / "reports.json"),
                   JsonBlocklistStore(data_dir / "blocklist.json"))

    #raises ReportStorageError if reports.json is corrupt, a missing file gives an empty history
    def load_history(self) -> ReportHistory:
        return ReportHistory.from_dicts(self._report_repository.load_all())

    #True if saved, False if it failed
    def save_history(self, history: ReportHistory) -> bool:
        return self._report_repository.save_all(history.to_dicts())

    #raises ReportStorageError if blocklist.json is corrupt, a missing file gives an empty blocklist
    def load_blocklist(self):
        return self._blocklist_store.load()

    #True if saved, False if it failed
    def save_blocklist(self, blocklist) -> bool:
        return self._blocklist_store.save(blocklist)

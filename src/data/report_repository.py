"""report_repository: the contract every report storage must follow, whatever it saves to."""

from abc import ABC, abstractmethod


#interface: only abstract methods and no shared code, so any storage (JSON file, database, in-memory for tests)
#can be swapped in. the rest of the app only talks to this type, never to a specific storage class.
class ReportRepository(ABC):

    #returns every saved report as a list of dicts, [] if nothing is saved yet
    @abstractmethod
    def load_all(self) -> list:
        pass

    #replaces the saved reports with this list, True if it worked, False if it failed
    @abstractmethod
    def save_all(self, reports: list) -> bool:
        pass

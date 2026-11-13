"""dashboard_panel: the shared base for every dashboard panel, and the result each panel gives back."""

from abc import ABC, abstractmethod


class PanelResult:
    """What one panel found: a title, its (label, value) rows, and a note shown when there is nothing to count."""

    def __init__(self, title: str, rows: list[tuple[str, object]], note: str = ""):
        self._title = title
        # Stored as a tuple so the rows can't be changed after the panel has worked them out.
        self._rows = tuple(rows)
        self._note = note

    @property
    def title(self) -> str:
        return self._title

    @property
    def rows(self) -> list[tuple[str, object]]:
        return list(self._rows)

    @property
    def note(self) -> str:
        return self._note

    @property
    def is_empty(self) -> bool:
        return not self._rows


class DashboardPanel(ABC):
    """One dashboard panel. Each subclass sets TITLE and works out its own rows from the saved reports."""

    TITLE = "Panel"
    EMPTY_NOTE = "No reports saved yet."

    def build(self, reports: list[dict]) -> PanelResult:
        """Works out the panel for the saved reports. The same steps run for every panel; only the rows differ."""
        if not reports:
            return PanelResult(self.TITLE, [], self.EMPTY_NOTE)
        return PanelResult(self.TITLE, self.compute_rows(reports))

    @abstractmethod
    def compute_rows(self, reports: list[dict]) -> list[tuple[str, object]]:
        """Returns this panel's (label, value) rows. Every subclass must provide this."""
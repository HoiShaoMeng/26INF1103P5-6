"""dashboard: puts the dashboard panels together and works out every panel from the saved reports."""

from collections.abc import Callable
from datetime import datetime

from ai_availability_panel import AiAvailabilityPanel
from campaign_panel import CampaignPanel
from dashboard_panel import DashboardPanel, PanelResult
from severity_breakdown_panel import SeverityBreakdownPanel
from tactics_panel import TacticsPanel
from trend_panel import TrendPanel


class Dashboard:
    """Holds a list of panels and builds them all from the same saved reports, in order."""

    def __init__(self, panels: list[DashboardPanel]):
        self._panels = list(panels)

    @classmethod
    def standard(cls, model: str | None = None, clock: Callable[[], datetime] | None = None) -> "Dashboard":
        """Returns the dashboard the app shows: severity, trend, campaigns, tactics and AI availability."""
        return cls([SeverityBreakdownPanel(), TrendPanel(clock), CampaignPanel(clock),
                    TacticsPanel(), AiAvailabilityPanel(model)])

    def build(self, reports: list[dict]) -> list[PanelResult]:
        """Returns one result per panel. Each panel works out its own rows, so a new panel needs no change here."""
        return [panel.build(reports) for panel in self._panels]
"""ai_availability_panel: which AI model is set, and how often it answered or failed."""

from datetime import datetime, timedelta, timezone

from dashboard_panel import DashboardPanel
from severity_rules import AiUnavailableRule

# Singapore has no daylight saving time, so a fixed UTC+8 offset is always correct.
SINGAPORE_TIME = timezone(timedelta(hours=8), "SGT")


class AiAvailabilityPanel(DashboardPanel):
    """Shows the AI model, how many screenings the AI answered or failed, and when it last failed."""

    TITLE = "AI availability"
    # The same marker the severity rules use, so both always agree on what a failed AI call looks like.
    UNAVAILABLE = AiUnavailableRule.UNAVAILABLE_CLASSIFICATION

    def __init__(self, model: str | None = None):
        # The model name is passed in by whoever builds the dashboard, so this panel never reads the AI settings itself.
        self._model = model

    def compute_rows(self, reports: list[dict]) -> list[tuple[str, object]]:
        failed = [report for report in reports if report.get("classification") == self.UNAVAILABLE]
        total = len(reports)
        return [
            ("model", self._model or "unknown"),
            ("answered", self._share(total - len(failed), total)),
            ("unavailable", self._share(len(failed), total)),
            ("last_failure", self._last_failure(failed)),
        ]

    @staticmethod
    def _share(count: int, total: int) -> str:
        """Returns e.g. '18 of 20 (90%)'."""
        return f"{count} of {total} ({round(count * 100 / total)}%)"

    @staticmethod
    def _last_failure(failed: list[dict]) -> str:
        """Returns the Singapore time of the latest failed screening, or 'none' if the AI never failed."""
        times = []
        for report in failed:
            try:
                moment = datetime.fromisoformat(report.get("reported_at"))
            except (TypeError, ValueError):
                continue
            # A time saved without a zone is treated as Singapore time, the same way the report list shows it.
            times.append(moment if moment.tzinfo else moment.replace(tzinfo=SINGAPORE_TIME))
        if not times:
            return "none" if not failed else "unknown"
        return max(times).astimezone(SINGAPORE_TIME).strftime("%d %b %Y, %H:%M %Z")
"""trend_panel: how many emails were reported on each of the last 7 days."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone

from dashboard_panel import DashboardPanel

# Singapore has no daylight saving time, so a fixed UTC+8 offset is always correct.
SINGAPORE_TIME = timezone(timedelta(hours=8), "SGT")


class TrendPanel(DashboardPanel):
    """Counts the reports per day for the last 7 days in Singapore time, with a simple bar for each day."""

    TITLE = "Last 7 days"
    DAYS = 7
    MAX_BAR = 20

    def __init__(self, clock: Callable[[], datetime] | None = None):
        # Passed in so tests can fix "today" instead of depending on the real date.
        self._clock = clock or (lambda: datetime.now(UTC))

    def compute_rows(self, reports: list[dict]) -> list[tuple[str, object]]:
        today = self._clock().astimezone(SINGAPORE_TIME).date()
        days = [today - timedelta(days=offset) for offset in range(self.DAYS - 1, -1, -1)]
        counts = dict.fromkeys(days, 0)
        for report in reports:
            day = self._report_day(report.get("reported_at"))
            if day in counts:
                counts[day] += 1

        # The bars are shrunk only when a busy day would make them too long to fit on the screen.
        busiest = max(counts.values())
        scale = self.MAX_BAR / busiest if busiest > self.MAX_BAR else 1
        rows = [(day.isoformat(), f"{count}  {'#' * round(count * scale)}".rstrip()) for day, count in counts.items()]
        rows.append(("total", sum(counts.values())))
        return rows

    @staticmethod
    def _report_day(value):
        """Returns the Singapore date a report was made, or None if its time is missing or not a valid timestamp."""
        try:
            moment = datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None
        # A time saved without a zone is treated as Singapore time, the same way the report list shows it.
        if moment.tzinfo is None:
            return moment.date()
        return moment.astimezone(SINGAPORE_TIME).date()
"""campaign_panel: the phishing campaigns still active, meaning seen in the last 24 hours."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone

from dashboard_panel import DashboardPanel

# Singapore has no daylight saving time, so a fixed UTC+8 offset is always correct.
SINGAPORE_TIME = timezone(timedelta(hours=8), "SGT")


class CampaignPanel(DashboardPanel):
    """Lists the sender domains with 3 or more reports in the last 24 hours, busiest first."""

    TITLE = "Active campaigns"
    # The same rule the campaign check uses: 3+ reports from one sender or domain within 24 hours.
    MIN_REPORTS = 3
    WINDOW = timedelta(hours=24)

    def __init__(self, clock: Callable[[], datetime] | None = None):
        # Passed in so tests can fix "now" instead of depending on the real time.
        self._clock = clock or (lambda: datetime.now(UTC))

    def compute_rows(self, reports: list[dict]) -> list[tuple[str, object]]:
        now = self._clock()
        # domain -> times of its reports in the last 24 hours
        recent: dict[str, list[datetime]] = {}
        for report in reports:
            domain = self._domain(report.get("sender_email"))
            moment = self._time(report.get("reported_at"))
            if domain and moment and timedelta(0) <= now - moment <= self.WINDOW:
                recent.setdefault(domain, []).append(moment)

        campaigns = [(domain, times) for domain, times in recent.items() if len(times) >= self.MIN_REPORTS]
        if not campaigns:
            return [("active_campaigns", "none in the last 24 hours")]
        # Busiest first; a tie goes to the campaign seen most recently.
        campaigns.sort(key=lambda item: (len(item[1]), max(item[1])), reverse=True)
        return [(f"campaign_{number}", f"{domain}: {len(times)} reports, latest {self._show_time(max(times))}")
                for number, (domain, times) in enumerate(campaigns, start=1)]

    @staticmethod
    def _domain(sender_email):
        """Returns the lowercased domain of a sender email, or None if it is missing or not an email."""
        if not isinstance(sender_email, str) or "@" not in sender_email:
            return None
        return sender_email.strip().lower().rsplit("@", 1)[1] or None

    @staticmethod
    def _time(value):
        """Returns the report time with a zone (Singapore if none was saved), or None if it is not a valid time."""
        try:
            moment = datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None
        return moment if moment.tzinfo else moment.replace(tzinfo=SINGAPORE_TIME)

    @staticmethod
    def _show_time(moment: datetime) -> str:
        return moment.astimezone(SINGAPORE_TIME).strftime("%d %b %Y, %H:%M %Z")
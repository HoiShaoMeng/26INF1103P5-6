"""severity_breakdown_panel: how many saved reports there are of each severity."""

from collections import Counter

from dashboard_panel import DashboardPanel
from severity_rules import Severity


class SeverityBreakdownPanel(DashboardPanel):
    """Counts the saved reports per severity, highest first, with each count's share of the total."""

    TITLE = "Severity breakdown"

    def compute_rows(self, reports: list[dict]) -> list[tuple[str, object]]:
        counts = Counter(report.get("severity") for report in reports)
        total = len(reports)
        # The severities come from the Severity enum, so a new tier would show up here without changing this panel.
        known = [severity.value for severity in reversed(list(Severity))]
        rows = [(severity, self._count_text(counts[severity], total)) for severity in known]
        # Reports with a missing or unexpected severity are still counted, so the rows always add up to the total.
        other = total - sum(counts[severity] for severity in known)
        if other:
            rows.append(("other", self._count_text(other, total)))
        rows.append(("total", total))
        return rows

    @staticmethod
    def _count_text(count: int, total: int) -> str:
        """Returns e.g. '3 (50%)'."""
        return f"{count} ({round(count * 100 / total)}%)"
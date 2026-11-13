"""tactics_panel: the phishing tactics the AI spotted most often."""

from collections import Counter

from dashboard_panel import DashboardPanel


class TacticsPanel(DashboardPanel):
    """Lists the 5 most common tactics, with how many reports had each one."""

    TITLE = "Top tactics"
    TOP = 5

    def compute_rows(self, reports: list[dict]) -> list[tuple[str, object]]:
        counts = Counter()
        for report in reports:
            counts.update(self._tactics(report.get("tactics_detected")))
        if not counts:
            return [("tactics_detected", "none recorded")]
        total = len(reports)
        # Most common first; a tie is listed in alphabetical order, so the order never changes between runs.
        top = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:self.TOP]
        return [(tactic, f"{count} of {total} reports") for tactic, count in top]

    @staticmethod
    def _tactics(value) -> set[str]:
        """Returns one report's tactics, tidied and without repeats. Anything that is not a list of text is ignored."""
        if not isinstance(value, list):
            return set()
        # The tactics are saved as keys like 'urgency_pressure', so the screen can turn them into 'Urgency pressure'.
        return {tactic.strip().lower() for tactic in value if isinstance(tactic, str) and tactic.strip()}
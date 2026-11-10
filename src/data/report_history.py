"""report_history: the saved reports as one object, with the filter and sort queries the IT team uses."""

#a group of saved reports that can be filtered and sorted.
#aggregation: the history holds reports that already exist on their own (loaded from reports.json),
#it only groups them, so a report is not created or destroyed by the history.
class ReportHistory:

    def __init__(self, reports: list | None = None):
        #anything that is not a list (e.g. None) gives an empty history instead of crashing
        if not isinstance(reports, list):
            reports = []
        #private: only report dicts are kept, anything else in the file is skipped
        self._reports = [report for report in reports if isinstance(report, dict)]

    #read-only access: returns a copy of the list, so outside code cannot change the history by accident
    @property
    def reports(self) -> list:
        return list(self._reports)

    #lets len(history) give the number of saved reports
    def __len__(self) -> int:
        return len(self._reports)

    #filter/query: returns a new history with only the reports of the given severity, in saved order.
    #it never changes this history, and gives an empty history if nothing matches.
    def filter_by_severity(self, severity: str) -> "ReportHistory":
        #anything that is not a severity string cant be filtered, so return an empty history instead of crashing
        if not isinstance(severity, str):
            return ReportHistory()

        #saved severities are always like "NEEDS_REVIEW", so "needs review" or " critical " still match
        wanted_severity = severity.strip().upper().replace(" ", "_")

        matching_reports = []
        for report in self._reports:
            if report.get("severity") == wanted_severity:
                matching_reports.append(report)

        return ReportHistory(matching_reports)

    #query: returns a new history sorted from highest to lowest threat level, so the most dangerous are seen first.
    #reports with the same threat level keep their saved order (oldest first), because python's sort is stable.
    def sort_by_threat_level(self) -> "ReportHistory":
        sorted_reports = sorted(self._reports, key=self._threat_level_or_lowest, reverse=True)
        return ReportHistory(sorted_reports)

    #private helper for sorting: a report's threat level, or -1 if it is missing or not a number, so those go last
    @staticmethod
    def _threat_level_or_lowest(report: dict) -> float:
        threat_level = report.get("threat_level")
        if isinstance(threat_level, (int, float)):
            return threat_level
        return -1

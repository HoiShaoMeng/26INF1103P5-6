"""report_list_view: the boxed, numbered list of saved reports for one severity."""

from datetime import datetime, timedelta, timezone

from text_view import TextView

# Singapore has no daylight saving time, so a fixed UTC+8 offset is always correct.
SINGAPORE_TIME = timezone(timedelta(hours=8), "SGT")


class ReportListView(TextView):
    """Shows the saved reports of one severity. Missing fields show as 'unknown'."""

    WIDTH = 64

    def build_lines(self, reports: list[dict], severity: str) -> list[str]:
        """Builds the whole list: a title box, then one numbered block per report."""
        title = severity.replace("_", " ")
        heavy_line = "=" * self.WIDTH

        if not reports:
            return [heavy_line, f" {title} REPORTS", heavy_line, f" No {title} reports saved yet.", heavy_line]

        lines = [heavy_line, f" {title} REPORTS  ({len(reports)} saved, highest threat first)", heavy_line]
        for number, report in enumerate(reports, start=1):
            lines += self._build_report_lines(number, report)
        lines.append("")
        lines.append(heavy_line)
        return lines

    def _build_report_lines(self, number: int, report: dict) -> list[str]:
        """Builds one report's block: its number, time and id, then its aligned fields."""
        fields = self._report_fields(report)
        label_width = max(len(self.format_label(key)) for key, _ in fields) + 2
        report_id = report.get("report_id")
        id_text = f"   id {report_id}" if report_id else ""
        return ["",
                f" [{number}]  {self.format_timestamp(report.get('reported_at'))}{id_text}",
                "-" * self.WIDTH,
                *["   " + line for line in self.format_section(fields, label_width)]]

    def _report_fields(self, report: dict) -> list[tuple[str, object]]:
        """Picks the fields to show for one report, adding the review and re-check note only when there is one."""
        sender_email = self.format_value(report.get("sender_email"))
        sender_name = report.get("sender_name")
        sender = f"{sender_name} <{sender_email}>" if sender_name else sender_email

        threat_level = report.get("threat_level")
        threat_text = f"{threat_level} / 100" if isinstance(threat_level, (int, float)) else self.format_value(threat_level)

        fields = [
            ("from", sender),
            ("subject", report.get("subject")),
            ("classification", report.get("classification")),
            ("threat_level", threat_text),
            ("campaign", report.get("is_campaign")),
            ("action", report.get("recommended_action")),
        ]
        review = report.get("review")
        if isinstance(review, dict):
            decision = str(review.get("decision", "")).replace("_", " ").lower()
            fields.append(("review", f"{decision} by {self.format_value(review.get('analyst'))}"))
        if report.get("flagged_by"):
            fields.append(("re_check", f"related to confirmed phishing report {report['flagged_by']}"))
        return fields

    @staticmethod
    def format_timestamp(value) -> str:
        """Turns a saved ISO timestamp into Singapore time, e.g. '2026-10-12T13:00:49+00:00' -> '12 Oct 2026, 21:00 SGT'."""
        try:
            moment = datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return TextView.format_value(value)
        if moment.tzinfo is None:
            return moment.strftime("%d %b %Y, %H:%M")
        return moment.astimezone(SINGAPORE_TIME).strftime("%d %b %Y, %H:%M %Z")
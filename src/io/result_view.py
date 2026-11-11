"""result_view: the boxed screening result shown after an email has been analysed."""

from text_view import TextView


class ResultView(TextView):
    """Shows one screening result: the email, whatever fields the AI returned, and the triage decision."""

    def build_lines(self, record: dict, ai_result: dict | None, severity: str,
                    action: str, is_campaign: bool = False) -> list[str]:
        """Builds the screening result from the record, the AI's fields and logic's decision."""
        # Shows whatever fields the AI returned (no fixed list), so a renamed AI field still displays.
        ai_fields = list(ai_result.items()) if isinstance(ai_result, dict) and ai_result else [("ai_result", None)]
        sections = [
            [
                ("sender", f"{record['sender_name']} <{record['sender_email']}>".strip()),
                ("subject", record["subject"]),
                ("reported_at", record["reported_at"]),
            ],
            ai_fields,
            [
                ("campaign", is_campaign),
                ("severity", severity),
                ("recommended_action", action),
            ],
        ]

        # Longest label + 2 spaces, so every value starts in the same column.
        label_width = max(len(self.format_label(key)) for section in sections for key, _ in section) + 2
        blocks = [self.format_section(section, label_width) for section in sections]
        # Divider lines are as wide as the longest line.
        width = max(len(line) for block in blocks for line in block)

        lines = ["=" * width, "SCREENING RESULT", "=" * width]
        for index, block in enumerate(blocks):
            if index > 0:
                lines.append("-" * width)
            lines += block
        lines.append("=" * width)
        return lines
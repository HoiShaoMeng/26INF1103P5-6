from text_view import TextView


class DashboardView(TextView):
    WIDTH = 64

    def build_lines(self, results: list) -> list[str]:
        """Builds the whole dashboard from the panels' results (each has a title, rows and a note)."""
        heavy_line = "=" * self.WIDTH
        # One label width for every panel, so all the values on the screen start in the same column.
        labels = [self.format_label(key) for result in results for key, _ in result.rows]
        label_width = max((len(label) for label in labels), default=0) + 2

        lines = [heavy_line, " DASHBOARD", heavy_line]
        for result in results:
            lines += ["", f" {result.title}", "-" * self.WIDTH]
            if result.rows:
                lines += ["   " + line for line in self.format_section(result.rows, label_width)]
            else:
                lines.append(f"   {result.note}")
        lines += ["", heavy_line]
        return lines
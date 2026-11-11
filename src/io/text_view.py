"""text_view: the shared base for screens that print a block of aligned 'Label: value' lines."""

from abc import ABC, abstractmethod
from collections.abc import Callable


class TextView(ABC):
    """A screen made of text lines. Each subclass decides its own lines; this class formats and prints them."""

    def __init__(self, print_line: Callable[[str], None] = print):
        # Passed in so tests can collect the lines instead of printing them.
        self._print_line = print_line

    @abstractmethod
    def build_lines(self, *args, **kwargs) -> list[str]:
        """Returns the screen's lines without printing them. Every subclass must provide this."""

    def show(self, *args, **kwargs) -> None:
        """Prints a blank line, then the screen built by the subclass."""
        self._print_line("")
        for line in self.build_lines(*args, **kwargs):
            self._print_line(line)

    @staticmethod
    def format_label(key: str) -> str:
        """Turns a data key into a label, e.g. 'threat_level' -> 'Threat level'."""
        return key.replace("_", " ").capitalize()

    @staticmethod
    def format_value(value) -> str:
        """Turns any value into display text based on its type, not on its field name."""
        if value is None:
            return "unknown"
        # Checked early so True/False show as YES/no instead of "True"/"False"
        if isinstance(value, bool):
            return "YES" if value else "no"
        if isinstance(value, dict):
            return ", ".join(TextView.format_value(item) for item in value.values())
        if isinstance(value, list):
            return ", ".join(TextView.format_value(item) for item in value) or "none"
        return str(value)

    @staticmethod
    def format_section(fields: list[tuple[str, object]], label_width: int) -> list[str]:
        """Returns aligned 'Label: value' lines for a list of (key, value) pairs."""
        return [f"{TextView.format_label(key) + ':':<{label_width}}{TextView.format_value(value)}"
                for key, value in fields]
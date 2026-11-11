"""error_view: formats and prints error messages, so every layer reports problems the same way."""

from collections.abc import Callable

ERROR_PREFIX = "  [!]"


class ErrorView:
    """Shows errors. The print function is passed in, so tests can collect the lines instead of printing."""

    def __init__(self, print_line: Callable[[str], None] = print):
        self._print_line = print_line

    @staticmethod
    def format_message(source: str, problem, next_step: str = "") -> str:
        """Returns one error line, e.g. '  [!] AI error: request timed out. Perform a manual check within 24 hours.'"""
        # str() so an exception object can be passed in as the problem, not just text.
        message = f"{ERROR_PREFIX} {source} error: {str(problem).rstrip('.')}."
        if next_step:
            message += f" {next_step}"
        return message

    @staticmethod
    def format_input_error(message: str) -> str:
        """Returns a rejection line for typed input, e.g. '  [!] Subject is required.'"""
        return f"{ERROR_PREFIX} {message}"

    def show(self, source: str, problem, next_step: str = "") -> None:
        """Prints an error from any layer; the caller supplies the problem and what happens next."""
        self._print_line(self.format_message(source, problem, next_step))

    def show_input_error(self, message: str) -> None:
        """Prints why a typed value was rejected."""
        self._print_line(self.format_input_error(message))
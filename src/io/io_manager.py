"""io_manager: the IO Manager, the one place the app reads from and writes to the terminal."""

from collections.abc import Callable
from typing import ClassVar

from email_prompt import EmailPrompt
from error_view import ErrorView
from input_validator import InputValidator
from loading_indicator import LoadingIndicator
from menu_prompt import MenuPrompt
from report_list_view import ReportListView
from result_view import ResultView


class IOManager:
    """Collects and validates user input, and shows results, lists and errors. No business logic lives here."""

    MENU_TITLE = "Phishing Triage Assistant"
    MENU_OPTIONS: ClassVar[dict] = {"1": "Screen a new email", "2": "View saved reports by severity",
                                    "3": "Review a saved report", "4": "Exit"}
    # Must match the severities logic_manager returns and data_manager saves.
    SEVERITY_OPTIONS: ClassVar[dict] = {"1": "CRITICAL", "2": "NEEDS_REVIEW", "3": "LOG_ONLY"}
    # reported_at is left out so the same email always gives the AI the same input.
    AI_INPUT_FIELDS = ("sender_email", "sender_name", "subject", "body", "urls", "attachments")

    def __init__(self, read_input: Callable[[str], str] = input, print_line: Callable[[str], None] = print,
                 output=None):
        # Passed in so tests can fake the typing and collect the printed lines.
        self._read_input = read_input
        # Composition: the manager creates and owns these objects; they exist only to serve this manager.
        self._loading = LoadingIndicator(output=output)
        # Errors print through the indicator, so the loading dots are cleared first and each message gets its own line.
        self._error_view = ErrorView(self._loading.print_message)
        self._validator = InputValidator()
        self._result_view = ResultView(print_line)
        self._report_list_view = ReportListView(print_line)

    # --- Input ---
    def read_line(self, prompt: str) -> str:
        """Reads one line from the user, stripped of surrounding whitespace."""
        return self._read_input(prompt).strip()

    def show_error(self, message: str) -> None:
        """Prints why a typed value was rejected."""
        self._error_view.show_input_error(message)

    def prompt_menu_choice(self) -> str:
        """Shows the main menu and returns the chosen number, e.g. '1'."""
        return MenuPrompt(self.MENU_TITLE, self.MENU_OPTIONS, self.read_line, self.show_error).ask()

    def prompt_severity_choice(self) -> str:
        """Asks which severity to view and returns it in the saved form, e.g. 'NEEDS_REVIEW'."""
        return MenuPrompt("View saved reports", self.SEVERITY_OPTIONS, self.read_line, self.show_error).ask_label()

    def prompt_email_fields(self) -> dict:
        """Collects one reported email from the user and returns it as a record."""
        # read_raw keeps the body lines exactly as typed; every other answer is stripped.
        return EmailPrompt(self._validator, self.read_line, self.show_error, read_raw=self._read_input).ask()

    @classmethod
    def get_ai_input(cls, record: dict) -> dict:
        """Returns only the fields the AI should see."""
        return {field: record[field] for field in cls.AI_INPUT_FIELDS}

    # --- Output ---
    def display_screening_result(self, record: dict, ai_result: dict | None, severity: str,
                                 action: str, is_campaign: bool = False) -> None:
        """Prints the full screening result for one reported email."""
        self._result_view.show(record, ai_result, severity, action, is_campaign)

    def display_report_list(self, reports: list[dict], severity: str) -> None:
        """Prints the saved reports that match the chosen severity."""
        self._report_list_view.show(reports, severity)

    def display_error(self, source: str, problem, next_step: str = "") -> None:
        """Prints an error from any layer; the caller supplies the problem and what happens next."""
        self._error_view.show(source, problem, next_step)

    def run_with_loading(self, message: str, task, *args):
        """Runs task(*args) while animated dots show it is busy, then returns the task's result."""
        return self._loading.run(message, task, *args)


# Temporary bridge: main.py and the AI files still call these module names. They all use one shared
# IOManager, and can be deleted once those files create and use an IOManager object themselves.
_shared = IOManager()
MENU_OPTIONS = IOManager.MENU_OPTIONS
SEVERITY_OPTIONS = IOManager.SEVERITY_OPTIONS
read_line = _shared.read_line
show_error = _shared.show_error
prompt_menu_choice = _shared.prompt_menu_choice
prompt_severity_choice = _shared.prompt_severity_choice
prompt_email_fields = _shared.prompt_email_fields
get_ai_input = IOManager.get_ai_input
display_screening_result = _shared.display_screening_result
display_report_list = _shared.display_report_list
display_error = _shared.display_error
run_with_loading = _shared.run_with_loading
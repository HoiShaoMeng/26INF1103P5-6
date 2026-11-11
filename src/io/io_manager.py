"""io_manager: collects and validates reported-email input from the terminal."""

from email_prompt import EmailPrompt
from error_view import ErrorView
from input_validator import InputValidator
from loading_indicator import LoadingIndicator
from menu_prompt import MenuPrompt
from report_list_view import ReportListView
from result_view import ResultView

# One validator shared by every prompt in this file.
validator = InputValidator()
result_view = ResultView()
report_list_view = ReportListView()

def read_line(prompt: str) -> str:
    """Reads one line from the user, stripped off surrounding whitespace."""
    return input(prompt).strip()


def show_error(message: str) -> None:
    """Prints a rejection message."""
    error_view.show_input_error(message)


AI_INPUT_FIELDS = ("sender_email", "sender_name", "subject", "body", "urls", "attachments")


def get_ai_input(record: dict) -> dict:
    """Returns only the fields the AI should see. reported_at is left out so the same email always gives the AI the same input."""
    return {field: record[field] for field in AI_INPUT_FIELDS}


def prompt_email_fields() -> dict:
    """Collects one reported email from the user and returns it as a record."""
    return EmailPrompt(validator, read_line, show_error).ask()


def display_record_summary(record: dict) -> None:
    """Prints a short summary of a captured record so the user can confirm it."""
    print("\n--- Captured report ---")
    print(f"Sender:      {record['sender_name'] or '(no display name)'} <{record['sender_email']}>")
    print(f"Subject:     {record['subject']}")
    print(f"Body:        {len(record['body'].splitlines())} line(s)")
    print(f"URLs:        {', '.join(record['urls']) or 'none'}")
    names = [attachment["filename"] for attachment in record["attachments"]]
    print(f"Attachments: {', '.join(names) or 'none'}")
    print(f"Reported at: {record['reported_at']}")


# --- Display results ---
def display_screening_result(record: dict, ai_result: dict | None, severity: str,
                             action: str, is_campaign: bool = False) -> None:
    """Prints the full screening result for one reported email."""
    result_view.show(record, ai_result, severity, action, is_campaign)


# --- Error messages ---
def display_error(source: str, problem: str, next_step: str = "") -> None:
    """Prints an error from any layer; the caller supplies the problem and what happens next."""
    error_view.show(source, problem, next_step)



# --- Menu and saved reports view ---
MENU_OPTIONS = {"1": "Screen a new email", "2": "View saved reports by severity",
                "3": "Review a saved report", "4": "Exit"}

# Must match the severities logic_manager returns and data_manager saves.
SEVERITY_OPTIONS = {"1": "CRITICAL", "2": "NEEDS_REVIEW", "3": "LOG_ONLY"}


def prompt_menu_choice() -> str:
    """Shows the main menu and returns '1' (screen), '2' (view reports), '3' (review) or '4' (exit)."""
    return MenuPrompt("Phishing Triage Assistant", MENU_OPTIONS, read_line, show_error).ask()

def prompt_severity_choice() -> str:
    """Asks which severity to view and returns it in the saved form, e.g. 'NEEDS_REVIEW'."""
    return MenuPrompt("View saved reports", SEVERITY_OPTIONS, read_line, show_error).ask_label()


def display_report_list(reports: list[dict], severity: str) -> None:
    """Prints the saved reports that match the chosen severity."""
    report_list_view.show(reports, severity)


# --- Loading animation ---
# One indicator shared by the whole program, so errors and the dots never print over each other.
loading = LoadingIndicator()
# Errors print through the indicator, so the loading dots are cleared first and each message gets its own line.
error_view = ErrorView(loading.print_message)

def run_with_loading(message: str, task, *args):
    """Runs task(*args) while animated dots show it is busy, then returns the task's result."""
    return loading.run(message, task, *args)


if __name__ == "__main__":
    # Manual test harness: python src/io/io_manager.py
    test_record = prompt_email_fields()
    display_record_summary(test_record)
    print("\nAI will receive:", list(get_ai_input(test_record).keys()))
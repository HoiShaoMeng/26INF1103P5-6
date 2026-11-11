"""io_manager: collects and validates reported-email input from the terminal."""

from datetime import datetime, timedelta, timezone

from email_prompt import EmailPrompt
from error_view import ErrorView
from input_validator import InputValidator
from loading_indicator import LoadingIndicator
from menu_prompt import MenuPrompt
from result_view import ResultView
from text_view import TextView

# One validator shared by every prompt in this file.
validator = InputValidator()
result_view = ResultView()

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


# --- Output format ---
# The shared formatting now lives in TextView. These names stay until the report list gets its own view.
format_label = TextView.format_label
format_value = TextView.format_value
format_section = TextView.format_section

# A fixed UTC+8 offset is always correct.
SINGAPORE_TIME = timezone(timedelta(hours=8), "SGT")

def format_timestamp(value) -> str:
    """Turns a saved ISO timestamp into Singapore time for display, e.g. '2026-10-12T13:00:49+00:00' -> '12 Oct 2026, 21:00 SGT'."""
    try:
        moment = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return format_value(value)
    if moment.tzinfo is None:
        return moment.strftime("%d %b %Y, %H:%M")
    return moment.astimezone(SINGAPORE_TIME).strftime("%d %b %Y, %H:%M %Z")


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
REPORT_LIST_WIDTH = 64

def build_report_list_lines(reports: list[dict], severity: str) -> list[str]:
    """Builds a boxed, numbered view of the saved reports (no printing). Missing fields show as 'unknown'."""
    title = severity.replace("_", " ")
    heavy_line = "=" * REPORT_LIST_WIDTH
    light_line = "-" * REPORT_LIST_WIDTH

    if not reports:
        return [heavy_line, f" {title} REPORTS", heavy_line, f" No {title} reports saved yet.", heavy_line]

    lines = [heavy_line, f" {title} REPORTS  ({len(reports)} saved, highest threat first)", heavy_line]
    for number, report in enumerate(reports, start=1):
        sender_email = format_value(report.get("sender_email"))
        sender_name = report.get("sender_name")
        sender = f"{sender_name} <{sender_email}>" if sender_name else sender_email

        threat_level = report.get("threat_level")
        threat_text = f"{threat_level} / 100" if isinstance(threat_level, (int, float)) else format_value(threat_level)

        fields = [
            ("from", sender),
            ("subject", report.get("subject")),
            ("classification", report.get("classification")),
            ("threat_level", threat_text),
            ("campaign", report.get("is_campaign")),
            ("action", report.get("recommended_action")),
        ]
        # Shows the analyst review and re-check note only when there is one.
        review = report.get("review")
        if isinstance(review, dict):
            decision = str(review.get("decision", "")).replace("_", " ").lower()
            fields.append(("review", f"{decision} by {format_value(review.get('analyst'))}"))
        if report.get("flagged_by"):
            fields.append(("re_check", f"related to confirmed phishing report {report['flagged_by']}"))
        label_width = max(len(format_label(key)) for key, _ in fields) + 2

        lines.append("")
        report_id = report.get("report_id")
        id_text = f"   id {report_id}" if report_id else ""
        lines.append(f" [{number}]  {format_timestamp(report.get('reported_at'))}{id_text}")
        lines.append(light_line)
        lines += ["   " + line for line in format_section(fields, label_width)]

    lines.append("")
    lines.append(heavy_line)
    return lines


def display_report_list(reports: list[dict], severity: str) -> None:
    """Prints the saved reports that match the chosen severity."""
    print()
    for line in build_report_list_lines(reports, severity):
        print(line)


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
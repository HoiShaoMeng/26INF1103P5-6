"""io_manager: collects and validates reported-email input from the terminal."""

import re
from datetime import datetime

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def read_line(prompt: str) -> str:
    """Reads one line from the user, stripped off surrounding whitespace."""
    return input(prompt).strip()


def show_error(message: str) -> None:
    """Prints a rejection message."""
    print(f"  [!] {message}")


def is_non_empty(value: str) -> bool:
    """Returns True if the value contains at least one non-space character."""
    return value.strip() != ""


def is_valid_email(value: str) -> bool:
    """Returns True if the value looks like name@domain.tld."""
    return EMAIL_PATTERN.match(value) is not None


def prompt_required(prompt: str, field_name: str) -> str:
    """Re-prompts until the user enters a non-empty value."""
    while True:
        value = read_line(prompt)
        if is_non_empty(value):
            return value
        show_error(f"{field_name} is required. Please try again.")


def prompt_sender_email() -> str:
    """Re-prompts until the user enters a well-formed sender email address."""
    while True:
        value = prompt_required("Sender email: ", "Sender email")
        if is_valid_email(value):
            return value.lower()
        show_error("That does not look like an email address (e.g. name@domain.com).")


def prompt_yes_no(prompt: str) -> bool:
    """Re-prompts until the user answers y or n. Returns True for yes."""
    while True:
        answer = read_line(f"{prompt} (y/n): ").lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        show_error("Please enter y or n.")


BODY_END_MARKER = "END"


def collect_multiline_body() -> str:
    """Collects body text line by line until the user types END on its own line. Blank lines inside the email are kept. Re-prompts if the body is empty."""
    while True:
        print(f"Body text (paste the email, then type {BODY_END_MARKER} on its own line to finish):")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == BODY_END_MARKER:
                break
            lines.append(line.rstrip())
        body = "\n".join(lines).strip()
        if is_non_empty(body):
            return body
        show_error("Body text is required. Please try again.")


def collect_urls() -> list[str]:
    """Optionally collects one or more URLs. Returns an empty list if none."""
    urls = []
    if not prompt_yes_no("Any URLs found in the email?"):
        return urls
    print("Enter one URL per line (blank line to finish):")
    while True:
        url = read_line("  URL: ")
        if url == "":
            break
        urls.append(url)
    return urls


def split_extension(filename: str) -> str:
    """Returns the final extension in lowercase, e.g. 'invoice.pdf.exe' -> 'exe'."""
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def collect_attachment_metadata() -> list[dict]:
    """Optionally collects attachment filenames only; contents are never read.

    Returns a list of {"filename": str, "extension": str}, possibly empty.
    """
    attachments = []
    if not prompt_yes_no("Any attachments?"):
        return attachments
    print("Enter one attachment filename per line (blank line to finish):")
    while True:
        filename = read_line("  Filename: ")
        if filename == "":
            break
        attachments.append({"filename": filename, "extension": split_extension(filename)})
    return attachments


def current_timestamp() -> str:
    """Returns the current time in ISO format, e.g. '2026-09-28T14:05:00'."""
    return datetime.now().isoformat(timespec="seconds")


def build_email_record(sender_email: str, sender_name: str, subject: str, body: str, urls: list[str], attachments: list[dict]) -> dict:
    """Packages validated fields into one record for the rest of the pipeline. reported_at is added automatically; logic_manager.check_campaign() needs it."""
    return {
        "sender_email": sender_email,
        "sender_name": sender_name,
        "subject": subject,
        "body": body,
        "urls": urls,
        "attachments": attachments,
        "reported_at": current_timestamp(),
    }


AI_INPUT_FIELDS = ("sender_email", "sender_name", "subject", "body", "urls", "attachments")


def get_ai_input(record: dict) -> dict:
    """Returns only the fields the AI should see. reported_at is left out so the same email always gives the AI the same input."""
    return {field: record[field] for field in AI_INPUT_FIELDS}


def prompt_email_fields() -> dict:
    """Collects one reported email from the user and returns it as a record."""
    print("\n=== Report a suspicious email ===")
    sender_email = prompt_sender_email()
    sender_name = read_line("Sender display name (optional, press Enter to skip): ")
    subject = prompt_required("Subject: ", "Subject")
    body = collect_multiline_body()
    urls = collect_urls()
    attachments = collect_attachment_metadata()
    return build_email_record(sender_email, sender_name, subject, body, urls, attachments)


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
RESULT_WIDTH = 50
LABEL_WIDTH = 18

SEVERITY_LABELS = {
    "CRITICAL": "[!!!] CRITICAL",
    "NEEDS_REVIEW": "[!!] NEEDS REVIEW",
    "LOG_ONLY": "[i] LOG ONLY",
}


def format_divider(char: str = "-") -> str:
    """Returns a full-width divider line, e.g. '-----...'."""
    return char * RESULT_WIDTH


def format_field(label: str, value: str) -> str:
    """Returns one aligned 'Label:  value' line."""
    return f"{label + ':':<{LABEL_WIDTH}}{value}"


def format_severity(severity: str) -> str:
    """Returns the display label for a severity, e.g. 'CRITICAL' -> '[!!!] CRITICAL'."""
    return SEVERITY_LABELS.get(severity, f"[?] {severity}")


def format_list(items: list[str] | None) -> str:
    """Joins a list into 'a, b, c', or returns 'none' if it is empty or missing."""
    return ", ".join(items or []) or "none"


def format_yes_no(value: bool) -> str:
    """Returns 'YES' for True and 'no' for False, so warnings stand out."""
    return "YES" if value else "no"


def format_threat_level(level: int | float | None) -> str:
    """Returns e.g. '92/100', or 'unknown' if the AI gave no usable number."""
    if isinstance(level, bool) or not isinstance(level, (int, float)):
        return "unknown"
    return f"{int(level)}/100"


def format_tactics(tactics: list[str] | None) -> str:
    """Turns ['urgency_pressure', ...] into 'urgency pressure, ...'."""
    return format_list([tactic.replace("_", " ") for tactic in tactics or []])


# --- Display results ---
AI_UNAVAILABLE = "AI_UNAVAILABLE"


def is_ai_result_usable(ai_result: dict | None) -> bool:
    """Returns False if the AI failed (None) or returned the AI_UNAVAILABLE placeholder."""
    return isinstance(ai_result, dict) and ai_result.get("classification") != AI_UNAVAILABLE


def build_result_lines(record: dict, ai_result: dict | None, severity: str,
                       action: str, is_campaign: bool = False) -> list[str]:
    """Builds the screening result as a list of display lines (no printing)."""
    sender = f"{record['sender_name'] or '(no display name)'} <{record['sender_email']}>"
    lines = [
        format_divider("="),
        " SCREENING RESULT",
        format_divider("="),
        format_field("Sender", sender),
        format_field("Subject", record["subject"]),
        format_divider(),
    ]

    if is_ai_result_usable(ai_result):
        lines += [
            format_field("Classification", str(ai_result.get("classification", "unknown"))),
            format_field("Threat level", format_threat_level(ai_result.get("threat_level"))),
            format_field("Tactics", format_tactics(ai_result.get("tactics_detected"))),
            format_field("Suspicious URLs", format_list(ai_result.get("suspicious_urls"))),
            format_field("Suspicious files", format_list(ai_result.get("suspicious_attachments"))),
            format_field("Domain mismatch", format_yes_no(bool(ai_result.get("sender_domain_mismatch")))),
        ]
    else:
        lines.append(format_field("AI assessment", "unavailable - needs manual review"))

    lines += [
        format_field("Campaign", format_yes_no(is_campaign)),
        format_divider(),
        format_field("Severity", format_severity(severity)),
        format_field("Action", action),
        format_divider("="),
    ]
    return lines


def display_screening_result(record: dict, ai_result: dict | None, severity: str,
                             action: str, is_campaign: bool = False) -> None:
    """Prints the full screening result for one reported email."""
    print()
    for line in build_result_lines(record, ai_result, severity, action, is_campaign):
        print(line)


# --- Error messages ---
def format_error_message(source: str, problem: str, next_step: str = "") -> str:
    """Returns one error line, e.g. '  [!] AI error: request timed out. Perform a manual check within 24 hours.'"""
    message = f"  [!] {source} error: {problem.rstrip('.')}."
    if next_step:
        message += f" {next_step}"
    return message


def display_error(source: str, problem: str, next_step: str = "") -> None:
    """Prints an error from any layer; the caller supplies the problem and what happens next."""
    print(format_error_message(source, problem, next_step))


if __name__ == "__main__":
    # Manual test harness: python src/io/io_manager.py
    test_record = prompt_email_fields()
    display_record_summary(test_record)
    print("\nAI will receive:", list(get_ai_input(test_record).keys()))
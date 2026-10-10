"""io_manager: collects and validates reported-email input from the terminal."""

import re
from datetime import UTC, datetime

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
    """Returns the current UTC time in ISO format, e.g. '2026-09-28T06:05:00+00:00'."""
    return datetime.now(UTC).isoformat(timespec="seconds")


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
def format_label(key: str) -> str:
    """Turns a data key into a label, e.g. 'threat_level' -> 'Threat level'."""
    return key.replace("_", " ").capitalize()


def format_value(value) -> str:
    """Turns any value into display text based on its type, not on its field name."""
    if value is None:
        return "unknown"
    if isinstance(value, bool):
        return "YES" if value else "no"
    if isinstance(value, dict):
        return ", ".join(format_value(item) for item in value.values())
    if isinstance(value, list):
        return ", ".join(format_value(item) for item in value) or "none"
    return str(value)


def format_section(fields: list[tuple[str, object]], label_width: int) -> list[str]:
    """Returns aligned 'Label: value' lines for a list of (key, value) pairs."""
    return [f"{format_label(key) + ':':<{label_width}}{format_value(value)}" for key, value in fields]


# --- Display results ---
def build_result_lines(record: dict, ai_result: dict | None, severity: str,
                       action: str, is_campaign: bool = False) -> list[str]:
    """Builds the screening result from the record, whatever fields the AI returned, and logic's decision."""
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

    label_width = max(len(format_label(key)) for section in sections for key, _ in section) + 2
    blocks = [format_section(section, label_width) for section in sections]
    width = max(len(line) for block in blocks for line in block)

    lines = ["=" * width, "SCREENING RESULT", "=" * width]
    for index, block in enumerate(blocks):
        if index > 0:
            lines.append("-" * width)
        lines += block
    lines.append("=" * width)
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
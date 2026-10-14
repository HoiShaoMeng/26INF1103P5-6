"""io_manager: collects and validates reported-email input from the terminal."""

import re
import sys
import threading
from datetime import UTC, datetime, timedelta, timezone
from urllib.parse import urlparse

# Text@text.text with no spaces: a quick sanity check.
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --- Expected input types ---
# One rule per record field: what it holds, if it is required, its maximum length,
# and (optionally) which format check it must pass. All input validation reads from here.
INPUT_RULES = {
    "sender_email": {"label": "Sender email", "type": "email address", "required": True,
                     "max_length": 254, "format": "email", "hint": "e.g. name@domain.com"},
    "sender_name": {"label": "Sender display name", "type": "text", "required": False,
                    "max_length": 100},
    "subject": {"label": "Subject", "type": "text", "required": True, "max_length": 200},
    "body": {"label": "Body text", "type": "multi-line text", "required": True,
             "max_length": 10000},
    "urls": {"label": "URL", "type": "http/https link", "required": False,
             "max_length": 2048, "format": "url",
             "hint": "must start with http:// or https:// and include a domain"},
    "attachments": {"label": "Attachment filename", "type": "filename", "required": False,
                    "max_length": 255, "format": "filename",
                    "hint": "enter a filename only, e.g. invoice.pdf"},
}


def describe_expected_input(field: str) -> str:
    """Returns what a field expects, e.g. 'text, required, max 200 characters'."""
    rule = INPUT_RULES[field]
    required = "required" if rule["required"] else "optional"
    return f"{rule['type']}, {required}, max {rule['max_length']} characters"


def read_line(prompt: str) -> str:
    """Reads one line from the user, stripped off surrounding whitespace."""
    return input(prompt).strip()


def show_error(message: str) -> None:
    """Prints a rejection message."""
    with loading_lock:
        clear_loading_line()
        print(f"  [!] {message}")


def is_non_empty(value: str) -> bool:
    """Returns True if the value contains at least one non-space character."""
    return value.strip() != ""


def is_valid_email(value: str) -> bool:
    """Returns True if the value looks like name@domain.tld."""
    return EMAIL_PATTERN.match(value) is not None


def is_valid_url(value: str) -> bool:
    """Returns True if the value is an http/https link with a domain."""
    parts = urlparse(value)
    return parts.scheme in ("http", "https") and parts.netloc != ""


# A "/" or "\" (or "." / "..") means the user typed a folder path, not a filename.
def is_valid_filename(value: str) -> bool:
    """Returns True if the value is a plain filename, not empty and not a folder path."""
    name = value.strip()
    return name not in ("", ".", "..") and "/" not in name and "\\" not in name


# Links a rule's "format" in INPUT_RULES to the function that checks it.
FORMAT_CHECKS = {"email": is_valid_email, "url": is_valid_url, "filename": is_valid_filename}


def get_input_error(field: str, value: str) -> str | None:
    """Checks a value against its rule in INPUT_RULES; returns an error message, or None if valid."""
    rule = INPUT_RULES[field]
    # Checks run in order: empty, then too long, then wrong format. An empty optional field is allowed.
    if not is_non_empty(value):
        return f"{rule['label']} is required." if rule["required"] else None
    if len(value) > rule["max_length"]:
        return f"{rule['label']} is too long (max {rule['max_length']} characters)."
    check = FORMAT_CHECKS.get(rule.get("format"))
    if check and not check(value):
        return f"Invalid {rule['label'].lower()}: {rule['hint']}."
    return None


def prompt_field(prompt: str, field: str) -> str:
    """Re-prompts until the value passes the field's rule in INPUT_RULES."""
    while True:
        value = read_line(prompt)
        error = get_input_error(field, value)
        if error is None:
            return value
        show_error(error)


# Lowercase so check_campaign() treats PayPal@x.com and paypal@x.com as the same sender.
def prompt_sender_email() -> str:
    """Re-prompts until the user enters a valid sender email address."""
    return prompt_field("Sender email: ", "sender_email").lower()


def prompt_yes_no(prompt: str) -> bool:
    """Re-prompts until the user answers y or n. Returns True for yes."""
    while True:
        answer = read_line(f"{prompt} (y/n): ").lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        show_error("Please enter y or n.")


# A blank line can't end the body, because real emails have blank lines between paragraphs.
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
        error = get_input_error("body", body)
        if error is None:
            return body
        show_error(error)


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
        error = get_input_error("urls", url)
        if error:
            show_error(error)
            continue
        urls.append(url)
    return urls


# Only the LAST extension counts: "invoice.pdf.exe" is really an .exe
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
        error = get_input_error("attachments", filename)
        if error:
            show_error(error)
            continue
        # Only the name is stored; the file is never opened, so a harmful attachment can't run.
        attachments.append({"filename": filename, "extension": split_extension(filename)})
    return attachments


# UTC so times from different laptops and Docker compare correctly in check_campaign(). Shown in SGT by format_timestamp()
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
    sender_name = prompt_field("Sender display name (optional, press Enter to skip): ", "sender_name")
    subject = prompt_field("Subject: ", "subject")
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
    # Checked early so True/False show as YES/no instead of "True"/"False"
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


# Singapore has no daylight saving time, so a fixed UTC+8 offset is always correct.
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
def build_result_lines(record: dict, ai_result: dict | None, severity: str,
                       action: str, is_campaign: bool = False) -> list[str]:
    """Builds the screening result from the record, whatever fields the AI returned, and logic's decision."""
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
    label_width = max(len(format_label(key)) for section in sections for key, _ in section) + 2
    blocks = [format_section(section, label_width) for section in sections]
    # Divider lines are as wide as the longest line.
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
    # Clear the loading dots first, so the message gets its own line.
    with loading_lock:
        clear_loading_line()
        print(format_error_message(source, problem, next_step))


# --- Menu and saved reports view ---
MENU_OPTIONS = {"1": "Screen a new email", "2": "View saved reports by severity", "3": "Exit"}

# Must match the severities logic_manager returns and data_manager saves.
SEVERITY_OPTIONS = {"1": "CRITICAL", "2": "NEEDS_REVIEW", "3": "LOG_ONLY"}

def prompt_choice(title: str, options: dict[str, str]) -> str:
    """Shows numbered options and re-prompts until the user picks one. Returns the chosen number, e.g. '2'."""
    print()
    print(f"=== {title} ===")
    for number, label in options.items():
        print(f"  {number}. {label}")
    while True:
        choice = read_line("Choose an option: ")
        if choice in options:
            return choice
        show_error(f"Please enter one of: {', '.join(options)}.")

def prompt_menu_choice() -> str:
    """Shows the main menu and returns '1' (screen), '2' (view reports) or '3' (exit)."""
    return prompt_choice("Phishing Triage Assistant", MENU_OPTIONS)

def prompt_severity_choice() -> str:
    """Asks which severity to view and returns it in the saved form, e.g. 'NEEDS_REVIEW'."""
    return SEVERITY_OPTIONS[prompt_choice("View saved reports", SEVERITY_OPTIONS)]

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
        label_width = max(len(format_label(key)) for key, _ in fields) + 2

        lines.append("")
        lines.append(f" [{number}]  {format_timestamp(report.get('reported_at'))}")
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
LOADING_INTERVAL = 0.4
# How wide the dots line on screen is (0 = nothing shown).
loading_state = {"width": 0}
# Stops the dots thread and an error message from printing at the same moment.
loading_lock = threading.Lock()


def clear_loading_line() -> None:
    """Wipes the loading line so the next output starts on a clean line."""
    if loading_state["width"]:
        # \r jumps back to the start of the line; the spaces overwrite the old dots.
        print("\r" + " " * loading_state["width"] + "\r", end="", flush=True)
        loading_state["width"] = 0


def animate_loading(message: str, stop: threading.Event) -> None:
    """Shows 'message.', 'message..', 'message...' in turn until stop is set (runs in a background thread)."""
    dots = 1
    while True:
        # :<3 pads to 3 characters, so going from "..." back to "." leaves no leftover dots.
        line = f"{message}{'.' * dots:<3}"
        with loading_lock:
            print("\r" + line, end="", flush=True)
            loading_state["width"] = len(line)
        if stop.wait(LOADING_INTERVAL):
            break
        # Cycles 1 -> 2 -> 3 -> 1 ...
        dots = dots % 3 + 1
    with loading_lock:
        clear_loading_line()


def run_with_loading(message: str, task, *args):
    """Runs task(*args) while animated dots show it is busy, then returns the task's result."""
    if not sys.stdout.isatty():
        print(f"{message}...")
        return task(*args)
    stop = threading.Event()
    loading = threading.Thread(target=animate_loading, args=(message, stop), daemon=True)
    loading.start()
    try:
        return task(*args)
    finally:
        stop.set()
        loading.join()


if __name__ == "__main__":
    # Manual test harness: python src/io/io_manager.py
    test_record = prompt_email_fields()
    display_record_summary(test_record)
    print("\nAI will receive:", list(get_ai_input(test_record).keys()))
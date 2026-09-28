from datetime import datetime
import re

"""io_manager: collects and validates reported-email input from the terminal."""


# Expected format for an email address.
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def read_line(prompt: str) -> str:
    """Reads one line from the user and removes surrounding whitespace."""
    return input(prompt).strip()


def show_error(message: str) -> None:
    """Displays an error message for invalid user input."""
    print(f"  [!] {message}")


def is_non_empty(value: str) -> bool:
    """Returns True if the value contains at least one non-space character."""
    return value.strip() != ""


def is_valid_email(value: str) -> bool:
    """Returns True if the value looks like a valid email address."""
    return EMAIL_PATTERN.match(value) is not None


def is_valid_datetime(value: str) -> bool:
    """
    Returns True if the value matches the expected date/time format.

    Expected format:
    YYYY-MM-DD HH:MM
    """
    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False


def is_valid_extension(value: str) -> bool:
    """Returns True if the attachment extension starts with a period."""
    return value.startswith(".") and len(value) > 1


def prompt_required(prompt: str, field_name: str) -> str:
    """
    Prompts the user until a non-empty string is entered.

    Expected input type:
    String
    """
    while True:
        value = read_line(prompt)

        if is_non_empty(value):
            return value

        show_error(f"{field_name} is required. Please try again.")


def prompt_sender_email() -> str:
    """
    Prompts the user until a valid sender email is entered.

    Expected input type:
    Email address
    """
    while True:
        value = prompt_required(
            "Suspected sender email: ",
            "Sender email"
        )

        if is_valid_email(value):
            return value.lower()

        show_error(
            "Invalid email address. "
            "Example: sender@example.com"
        )


def prompt_report_datetime() -> str:
    """
    Prompts the user until a valid report date/time is entered.

    Expected input type:
    Date/time in YYYY-MM-DD HH:MM format
    """
    while True:
        value = prompt_required(
            "Date/time reported (YYYY-MM-DD HH:MM): ",
            "Report date/time"
        )

        if is_valid_datetime(value):
            return value

        show_error(
            "Invalid date/time. "
            "Please use YYYY-MM-DD HH:MM."
        )


def prompt_attachment_filenames() -> list[str]:
    """
    Collects attachment filenames.

    The user can enter multiple filenames separated by commas.
    The user can enter 'none' if there are no attachments.

    Expected input type:
    Comma-separated strings
    """
    while True:
        value = read_line(
            "Attachment filenames (comma-separated, or 'none'): "
        )

        if not is_non_empty(value):
            show_error(
                "Attachment information is required. "
                "Enter filenames or 'none'."
            )
            continue

        if value.lower() == "none":
            return []

        filenames = [
            filename.strip()
            for filename in value.split(",")
            if filename.strip()
        ]

        if filenames:
            return filenames

        show_error("Please enter at least one filename or 'none'.")


def prompt_attachment_extensions() -> list[str]:
    """
    Collects attachment file extensions.

    The user can enter multiple extensions separated by commas.
    The user can enter 'none' if there are no attachments.

    Expected input type:
    Comma-separated file extensions
    """
    while True:
        value = read_line(
            "Attachment extensions (comma-separated, or 'none'): "
        )

        if not is_non_empty(value):
            show_error(
                "Attachment extension information is required. "
                "Enter extensions or 'none'."
            )
            continue

        if value.lower() == "none":
            return []

        extensions = [
            extension.strip().lower()
            for extension in value.split(",")
            if extension.strip()
        ]

        if all(is_valid_extension(extension) for extension in extensions):
            return extensions

        show_error(
            "Invalid extension. "
            "Extensions should start with a period, e.g. .pdf, .exe."
        )


def collect_reported_email() -> dict:
    """
    Collects and validates all information required for a reported email.

    Returns:
        dict: Validated reported-email information.
    """
    print("\n=== Phishing / Suspicious Email Report ===")

    reporter_name = prompt_required(
        "Reporter name: ",
        "Reporter name"
    )

    report_datetime = prompt_report_datetime()

    sender_email = prompt_sender_email()

    sender_display_name = prompt_required(
        "Sender display name: ",
        "Sender display name"
    )

    subject = prompt_required(
        "Email subject: ",
        "Email subject"
    )

    body = prompt_required(
        "Email body: ",
        "Email body"
    )

    attachment_filenames = prompt_attachment_filenames()

    attachment_extensions = prompt_attachment_extensions()

    return {
        "reporter_name": reporter_name,
        "report_datetime": report_datetime,
        "sender_email": sender_email,
        "sender_display_name": sender_display_name,
        "subject": subject,
        "body": body,
        "attachment_filenames": attachment_filenames,
        "attachment_extensions": attachment_extensions,
    }


def display_report(report: dict) -> None:
    """Displays the validated email report before sending it for analysis."""

    print("\n=== Report Received ===")
    print(f"Reporter: {report['reporter_name']}")
    print(f"Reported at: {report['report_datetime']}")
    print(f"Sender: {report['sender_display_name']} "
          f"<{report['sender_email']}>")
    print(f"Subject: {report['subject']}")
    print(
        f"Attachments: "
        f"{', '.join(report['attachment_filenames']) or 'None'}"
    )

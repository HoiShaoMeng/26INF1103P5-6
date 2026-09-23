"""io_manager: collects and validates reported-email input from the terminal."""

import re

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
"""Unit tests for EmailPrompt: every typed line is faked, so no keyboard is needed."""

import os
import sys
from datetime import UTC, datetime

# adds the src/io and src/domain folders to the path so we can import email_prompt.py and its Attachment.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "io"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "domain"))

from email_prompt import EmailPrompt  # type: ignore
from input_validator import InputValidator  # type: ignore

FIXED_TIME = datetime(2026, 11, 11, 8, 30, tzinfo=UTC)

# one complete, valid email: sender, name, subject, body lines, END, then the URL and attachment answers
VALID_EMAIL = ["alerts@paypa1.com", "PayPal", "Blocked funds",
               "Dear customer,", "", "Verify now.", "END",
               "y", "http://paypa1.com/login", "",
               "y", "notice.pdf.exe", ""]


# builds a prompt that "types" the given lines in order, and collects its error messages
def make_prompt(lines):
    typed = iter(lines)
    errors = []
    prompt = EmailPrompt(InputValidator(), lambda text: next(typed).strip(), errors.append,
                         read_raw=lambda text: next(typed), clock=lambda: FIXED_TIME)
    return prompt, errors


def test_valid_email_gives_the_full_record():
    prompt, errors = make_prompt(VALID_EMAIL)
    assert prompt.ask() == {
        "sender_email": "alerts@paypa1.com",
        "sender_name": "PayPal",
        "subject": "Blocked funds",
        "body": "Dear customer,\n\nVerify now.",
        "urls": ["http://paypa1.com/login"],
        "attachments": [{"filename": "notice.pdf.exe", "extension": "exe"}],
        "reported_at": "2026-11-11T08:30:00+00:00",
    }
    assert errors == []


def test_sender_email_is_saved_in_lowercase():
    prompt, _ = make_prompt(["Alerts@PayPa1.COM"] + VALID_EMAIL[1:])
    assert prompt.ask()["sender_email"] == "alerts@paypa1.com"


def test_invalid_sender_email_is_asked_again():
    prompt, errors = make_prompt(["not-an-email"] + VALID_EMAIL)
    assert prompt.ask()["sender_email"] == "alerts@paypa1.com"
    assert len(errors) == 1


def test_empty_subject_is_asked_again():
    prompt, errors = make_prompt(VALID_EMAIL[:2] + [""] + VALID_EMAIL[2:])
    assert prompt.ask()["subject"] == "Blocked funds"
    assert errors == ["Subject is required."]


def test_empty_body_is_asked_again():
    prompt, errors = make_prompt(VALID_EMAIL[:3] + ["", "END"] + VALID_EMAIL[3:])
    assert prompt.ask()["body"] == "Dear customer,\n\nVerify now."
    assert errors == ["Body text is required."]


def test_body_ends_on_end_in_any_case():
    lines = VALID_EMAIL[:3] + ["Hello", "end"] + VALID_EMAIL[7:]
    prompt, _ = make_prompt(lines)
    assert prompt.ask()["body"] == "Hello"


def test_no_urls_or_attachments_gives_empty_lists():
    prompt, _ = make_prompt(VALID_EMAIL[:7] + ["n", "n"])
    record = prompt.ask()
    assert record["urls"] == []
    assert record["attachments"] == []


def test_invalid_url_is_skipped_and_valid_one_kept():
    prompt, errors = make_prompt(VALID_EMAIL[:7] + ["y", "paypa1.com", "https://ok.com", "", "n"])
    assert prompt.ask()["urls"] == ["https://ok.com"]
    assert len(errors) == 1


def test_folder_path_is_rejected_as_an_attachment():
    prompt, errors = make_prompt(VALID_EMAIL[:7] + ["n", "y", "docs/a.pdf", "a.PDF", ""])
    assert prompt.ask()["attachments"] == [{"filename": "a.PDF", "extension": "pdf"}]
    assert len(errors) == 1


def test_yes_no_answer_is_asked_again():
    prompt, errors = make_prompt(VALID_EMAIL[:7] + ["maybe", "n", "n"])
    prompt.ask()
    assert errors == ["Please enter y or n."]
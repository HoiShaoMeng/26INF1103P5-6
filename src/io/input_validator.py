"""input_validator: checks reported-email input against the rule for each field."""

import re
from urllib.parse import urlparse

# Text@text.text with no spaces: a quick sanity check.
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# One rule per record field: what it holds, if it is required, its maximum length,
# and (optionally) which format check it must pass.
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


class InputValidator:
    """Checks a field's value against its rule. The rules are passed in, so they can be changed or tested."""

    def __init__(self, rules: dict | None = None):
        self._rules = rules if rules is not None else INPUT_RULES
        # Links a rule's "format" to the method that checks it.
        self._format_checks = {
            "email": self.is_valid_email,
            "url": self.is_valid_url,
            "filename": self.is_valid_filename,
        }

    @staticmethod
    def is_non_empty(value: str) -> bool:
        """Returns True if the value contains at least one non-space character."""
        return value.strip() != ""

    @staticmethod
    def is_valid_email(value: str) -> bool:
        """Returns True if the value looks like name@domain.tld."""
        return EMAIL_PATTERN.match(value) is not None

    @staticmethod
    def is_valid_url(value: str) -> bool:
        """Returns True if the value is an http/https link with a domain."""
        parts = urlparse(value)
        return parts.scheme in ("http", "https") and parts.netloc != ""

    # A "/" or "\" (or "." / "..") means the user typed a folder path, not a filename.
    @staticmethod
    def is_valid_filename(value: str) -> bool:
        """Returns True if the value is a plain filename, not empty and not a folder path."""
        name = value.strip()
        return name not in ("", ".", "..") and "/" not in name and "\\" not in name

    def describe(self, field: str) -> str:
        """Returns what a field expects, e.g. 'text, required, max 200 characters'."""
        rule = self._rules[field]
        required = "required" if rule["required"] else "optional"
        return f"{rule['type']}, {required}, max {rule['max_length']} characters"

    def get_error(self, field: str, value: str) -> str | None:
        """Checks a value against its rule; returns an error message, or None if valid."""
        rule = self._rules[field]
        # Checks run in order: empty, then too long, then wrong format. An empty optional field is allowed.
        if not self.is_non_empty(value):
            return f"{rule['label']} is required." if rule["required"] else None
        if len(value) > rule["max_length"]:
            return f"{rule['label']} is too long (max {rule['max_length']} characters)."
        check = self._format_checks.get(rule.get("format"))
        if check and not check(value):
            return f"Invalid {rule['label'].lower()}: {rule['hint']}."
        return None
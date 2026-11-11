"""email_prompt: asks the user for one reported email, field by field, and re-asks until each field is valid."""

from collections.abc import Callable
from datetime import UTC, datetime

from attachment import Attachment

# A blank line can't end the body, because real emails have blank lines between paragraphs.
BODY_END_MARKER = "END"


class EmailPrompt:
    """Collects one reported email. Input, errors and the clock are passed in, so tests can fake them."""

    def __init__(self, validator, read_input: Callable[[str], str], show_error: Callable[[str], None],
                 read_raw: Callable[[str], str] = input, clock: Callable[[], datetime] | None = None):
        self._validator = validator
        # read_input gives a stripped line; read_raw keeps the line as typed, for the email body.
        self._read_input = read_input
        self._show_error = show_error
        self._read_raw = read_raw
        self._clock = clock or (lambda: datetime.now(UTC))

    def ask(self) -> dict:
        """Asks for every field and returns one record for the rest of the pipeline."""
        print("\n=== Report a suspicious email ===")
        # Lowercase so the campaign check treats PayPal@x.com and paypal@x.com as the same sender.
        sender_email = self._ask_field("Sender email: ", "sender_email").lower()
        sender_name = self._ask_field("Sender display name (optional, press Enter to skip): ", "sender_name")
        subject = self._ask_field("Subject: ", "subject")
        body = self._ask_body()
        urls = self._ask_list("Any URLs found in the email?",
                              "Enter one URL per line (blank line to finish):", "  URL: ", "urls")
        filenames = self._ask_list("Any attachments?",
                                   "Enter one attachment filename per line (blank line to finish):",
                                   "  Filename: ", "attachments")
        return {
            "sender_email": sender_email,
            "sender_name": sender_name,
            "subject": subject,
            "body": body,
            "urls": urls,
            # Only the name is stored; the file is never opened, so a harmful attachment can't run.
            "attachments": [Attachment(name).to_dict() for name in filenames],
            # UTC so times from different laptops and Docker compare correctly in the campaign check.
            "reported_at": self._clock().isoformat(timespec="seconds"),
        }

    def _ask_field(self, prompt: str, field: str) -> str:
        """Re-asks until the value passes the field's rule."""
        while True:
            value = self._read_input(prompt)
            error = self._validator.get_error(field, value)
            if error is None:
                return value
            self._show_error(error)

    def _ask_yes_no(self, prompt: str) -> bool:
        """Re-asks until the user answers y or n. Returns True for yes."""
        while True:
            answer = self._read_input(f"{prompt} (y/n): ").lower()
            if answer in ("y", "yes"):
                return True
            if answer in ("n", "no"):
                return False
            self._show_error("Please enter y or n.")

    def _ask_body(self) -> str:
        """Collects the body line by line until END is typed on its own line. Re-asks if the body is empty."""
        while True:
            print(f"Body text (paste the email, then type {BODY_END_MARKER} on its own line to finish):")
            lines = []
            while True:
                line = self._read_raw("")
                if line.strip().upper() == BODY_END_MARKER:
                    break
                lines.append(line.rstrip())
            body = "\n".join(lines).strip()
            error = self._validator.get_error("body", body)
            if error is None:
                return body
            self._show_error(error)

    def _ask_list(self, question: str, instructions: str, prompt: str, field: str) -> list[str]:
        """Asks if there are any items, then collects valid ones until a blank line. Used for URLs and attachments."""
        items = []
        if not self._ask_yes_no(question):
            return items
        print(instructions)
        while True:
            value = self._read_input(prompt)
            if value == "":
                break
            error = self._validator.get_error(field, value)
            if error:
                self._show_error(error)
                continue
            items.append(value)
        return items
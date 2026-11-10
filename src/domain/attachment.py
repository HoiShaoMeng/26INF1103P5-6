"""attachment: one file attached to a reported email. Only its name is kept; the file is never opened."""


class Attachment:
    """The name of one attached file. It cannot change after creation, so its extension always matches."""

    def __init__(self, filename: str):
        self._filename = filename

    @property
    def filename(self) -> str:
        """The name exactly as the user typed it."""
        return self._filename

    @property
    def extension(self) -> str:
        """The final extension in lowercase, e.g. 'invoice.pdf.exe' -> 'exe'. Empty if there is none."""
        if "." not in self._filename:
            return ""
        return self._filename.rsplit(".", 1)[1].lower()

    def to_dict(self) -> dict:
        """Returns the saved form used in reports.json."""
        return {"filename": self.filename, "extension": self.extension}

    @classmethod
    def from_dict(cls, data: dict) -> "Attachment":
        """Rebuilds an Attachment from its saved form. The extension is worked out again from the name."""
        return cls(data["filename"])
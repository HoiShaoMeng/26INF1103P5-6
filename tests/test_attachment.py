"""Unit tests for Attachment: covers the extension rule and the saved format."""

import os
import sys

import pytest

#adds the src/domain folder to the path so we can import attachment.py for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "domain"))

from attachment import Attachment  # type: ignore


@pytest.mark.parametrize("filename, expected", [
    ("invoice.pdf", "pdf"),
    ("Blocked_Funds_Notice.pdf.exe", "exe"),
    ("REPORT.DOCX", "docx"),
    ("README", ""),
    ("archive.", ""),
])
def test_extension_is_the_last_part_in_lowercase(filename, expected):
    assert Attachment(filename).extension == expected


def test_filename_keeps_what_the_user_typed():
    assert Attachment("REPORT.DOCX").filename == "REPORT.DOCX"


def test_extension_cannot_be_changed():
    attachment = Attachment("invoice.pdf")
    with pytest.raises(AttributeError):
        attachment.extension = "txt"


def test_filename_cannot_be_changed():
    attachment = Attachment("invoice.pdf")
    with pytest.raises(AttributeError):
        attachment.filename = "other.pdf"


def test_to_dict_matches_the_saved_format():
    assert Attachment("a.pdf.exe").to_dict() == {"filename": "a.pdf.exe", "extension": "exe"}


def test_from_dict_rebuilds_the_same_attachment():
    saved = {"filename": "Notice.pdf.exe", "extension": "exe"}
    assert Attachment.from_dict(saved).to_dict() == saved
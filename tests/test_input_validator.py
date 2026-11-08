"""Unit tests for InputValidator: no typing needed, every value is passed in directly."""

import os
import sys

import pytest

# adds the src/io folder to the path so we can import input_validator.py for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "io"))

from input_validator import InputValidator  # type: ignore


@pytest.fixture
def validator():
    return InputValidator()


@pytest.mark.parametrize("value", ["alice@example.com", "a.b@mail.co.uk"])
def test_valid_email_is_accepted(validator, value):
    assert validator.get_error("sender_email", value) is None


@pytest.mark.parametrize("value", ["alice", "alice@", "@example.com", "a b@example.com"])
def test_invalid_email_is_rejected(validator, value):
    assert validator.get_error("sender_email", value).startswith("Invalid sender email")


def test_required_field_cannot_be_empty(validator):
    assert validator.get_error("subject", "   ") == "Subject is required."


def test_optional_field_can_be_empty(validator):
    assert validator.get_error("sender_name", "") is None


def test_value_over_max_length_is_rejected(validator):
    assert "too long" in validator.get_error("subject", "x" * 201)


def test_value_at_max_length_is_accepted(validator):
    assert validator.get_error("subject", "x" * 200) is None


@pytest.mark.parametrize("value", ["https://example.com", "http://a.b/path?q=1"])
def test_valid_url_is_accepted(validator, value):
    assert validator.get_error("urls", value) is None


@pytest.mark.parametrize("value", ["example.com", "ftp://example.com", "https://"])
def test_invalid_url_is_rejected(validator, value):
    assert validator.get_error("urls", value) is not None


@pytest.mark.parametrize("value", ["invoice.pdf", "setup.exe"])
def test_plain_filename_is_accepted(validator, value):
    assert validator.get_error("attachments", value) is None


@pytest.mark.parametrize("value", [r"C:\Users\a.pdf", "docs/a.pdf", ".", ".."])
def test_folder_path_is_rejected(validator, value):
    assert validator.get_error("attachments", value) is not None


def test_describe_lists_type_required_and_length(validator):
    assert validator.describe("subject") == "text, required, max 200 characters"


def test_custom_rules_are_used():
    rules = {"code": {"label": "Code", "type": "text", "required": True, "max_length": 3}}
    assert "too long" in InputValidator(rules).get_error("code", "abcd")
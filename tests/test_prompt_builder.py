"""Unit tests for PromptBuilder: the typed answers are faked, so no keyboard is needed."""

import os
import sys

import pytest

# adds the src/ai folder to the path so we can import prompt_builder.py for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ai"))

from prompt_builder import PromptBuilder  # type: ignore
from prompt_config import PromptConfig  # type: ignore


@pytest.fixture
def config():
    return PromptConfig(
        model = "test-model",
        temperature = 0,
        allowed_classifications=["phishing", "benign"],
        tactics_vocabulary=["impersonation", "urgency_pressure"],
        threat_level_range=[0, 100],
        output_fields={"classification": {"type": "string", "description": "one of allowed_classifications"}},
        rules=["Output JSON only"]
    )

@pytest.fixture
def builder(config):
    return PromptBuilder(config)

@pytest.fixture
def email():
    return {
        "sender_email": "alice@example.com",
        "sender_name": "Alice",
        "subject": "Reset your password",
        "body": "Click the link below.",
        "urls": ["http://bad.example.com", "http://worse.example.com"],
        "attachments": [{"filename": "invoice.pdf", "extension": ".pdf"}]
    }

    # system prompt tests

def test_system_prompt_starts_with_role_and_json_instruction(builder):
    system_prompt = builder.build_system_prompt()
    assert system_prompt.startswith("You are a phishing detection assistant. ")
    assert "Respond ONLY with valid JSON" in system_prompt

def test_system_prompt_includes_every_config_value(builder):
    system_prompt = builder.build_system_prompt()
    assert "\"classification\": ['phishing', 'benign']" in system_prompt
    assert "\"tactics_detected\": ['impersonation', 'urgency_pressure']" in system_prompt
    assert "\"output_fields_rules\": {'classification':" in system_prompt
    assert "\"rule\": ['Output JSON only']" in system_prompt

def test_system_prompt_shows_threat_level_range_as_a_list(builder):
    system_prompt = builder.build_system_prompt()
    assert "\"threat_level\": [0, 100]" in system_prompt

def test_system_prompt_is_the_same_every_time(builder):
    assert builder.build_system_prompt() == builder.build_system_prompt()

def test_system_prompt_builds_from_real_config_file():
    config = PromptConfig.load_from_yaml_file()
    builder = PromptBuilder(config)
    system_prompt = builder.build_system_prompt()
    assert "phishing" in system_prompt
    assert "credential_harvesting" in system_prompt

#   user prompt tests

def test_user_prompt_lists_every_email_field(builder, email):
    assert builder.build_user_prompt(email) == (
        "Sender email: alice@example.com\n"
        "Sender name: Alice\n"
        "Subject: Reset your password\n"
        "Body: Click the link below.\n"
        "URLs: http://bad.example.com, http://worse.example.com\n"
        "Attachments: invoice.pdf\n"
    )

def test_user_prompt_shows_none_for_empty_urls_and_attachments(builder, email):
    email["urls"] = []
    email["attachments"] = []
    user_prompt = builder.build_user_prompt(email)
    assert "URLs: none" in user_prompt
    assert "Attachments: none" in user_prompt

def test_user_prompt_shows_none_when_urls_and_attachments_are_missing(builder, email):
    del email["urls"]
    del email["attachments"]
    user_prompt = builder.build_user_prompt(email)
    assert "URLs: none" in user_prompt
    assert "Attachments: none" in user_prompt

def test_user_prompt_uses_attachment_filename_only(builder, email):
    email["attachments"] = [{"filename": "a.exe", "extension": ".exe"}, {"filename": "b.zip"}]
    user_prompt = builder.build_user_prompt(email)
    assert "Attachments: a.exe, b.zip" in user_prompt

def test_user_prompt_does_not_change_the_email(builder, email):
    original_email = email.copy()
    builder.build_user_prompt(email)
    assert email == original_email
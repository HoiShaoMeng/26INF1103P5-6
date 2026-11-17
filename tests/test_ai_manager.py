"""Unit tests for AIManager: the real prompt config and validator, with a fake AI client (no API key or network)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ai"))

from ai_manager import AI_UNAVAILABLE, AIManager  # type: ignore
from exceptions import (  # type: ignore
    AIConnectionError,
    MalformedResponseError,
    SchemaValidationError,
)
from mock_ai_client import MockAIClient
from prompt_config import PromptConfig  # type: ignore

EMAIL = {
    "sender_email": "support@paypa1.com",
    "sender_name": "PayPal Support",
    "subject": "Verify your account",
    "body": "Click the link to avoid suspension.",
    "urls": ["http://paypa1.com/verify"],
    "attachments": [],
}
VALID_REPLY = {
    "classification": "phishing",
    "threat_level": 90,
    "tactics_detected": ["impersonation", "urgency_pressure"],
    "suspicious_urls": ["http://paypa1.com/verify"],
    "suspicious_attachments": [],
    "sender_domain_mismatch": True,
}


def make_manager(replies):
    client = MockAIClient(replies)
    return AIManager(PromptConfig.load_from_yaml_file(), client), client


def test_valid_reply_is_parsed_and_returned():
    manager, _ = make_manager([json.dumps(VALID_REPLY)])
    assert manager.assess(EMAIL) == VALID_REPLY


def test_prompts_sent_to_the_client_contain_the_email():
    manager, client = make_manager([json.dumps(VALID_REPLY)])
    manager.assess(EMAIL)
    system_prompt, user_prompt = client.calls[0]
    assert system_prompt
    assert "support@paypa1.com" in user_prompt
    assert "Verify your account" in user_prompt


@pytest.mark.parametrize("reply", ["this is not json", "", None])
def test_reply_that_is_not_json_raises_malformed_response(reply):
    manager, _ = make_manager([reply])
    with pytest.raises(MalformedResponseError):
        manager.assess(EMAIL)


@pytest.mark.parametrize("bad_reply", [
    {**VALID_REPLY, "classification": "probably phishing"},
    {**VALID_REPLY, "threat_level": 150},
    {key: value for key, value in VALID_REPLY.items() if key != "sender_domain_mismatch"},
    ["not", "an", "object"],
])
def test_reply_that_breaks_the_schema_raises_schema_error(bad_reply):
    manager, _ = make_manager([json.dumps(bad_reply)])
    with pytest.raises(SchemaValidationError):
        manager.assess(EMAIL)


def test_connection_error_from_the_client_is_passed_up():
    manager, _ = make_manager([AIConnectionError("Rate limit hit (429)")])
    with pytest.raises(AIConnectionError):
        manager.assess(EMAIL)


def test_unavailable_result_has_all_six_fields_and_a_safe_default():
    result = AIManager.unavailable_result()
    assert set(result) == set(VALID_REPLY)
    assert result["classification"] == AI_UNAVAILABLE
    assert result["threat_level"] == 50


def test_unavailable_result_is_a_new_dict_each_time():
    first = AIManager.unavailable_result()
    first["tactics_detected"].append("changed")
    assert AIManager.unavailable_result()["tactics_detected"] == []


def test_client_property_returns_the_client_it_was_given():
    manager, client = make_manager([])
    assert manager.client is client

"""Unit tests for MockAIClient, and the AI classes working together through it: no API key or network needed."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ai"))

from ai_client import ai_client  # type: ignore
from exceptions import AIConnectionError, SchemaValidationError  # type: ignore
from mock_ai_client import MockAIClient
from prompt_builder import PromptBuilder  # type: ignore
from prompt_config import PromptConfig  # type: ignore
from response_validator import ResponseValidator  # type: ignore

VALID_REPLY = json.dumps({
    "classification": "phishing",
    "threat_level": 80,
    "tactics_detected": ["impersonation"],
    "suspicious_urls": ["http://bad.example.com"],
    "suspicious_attachments": [],
    "sender_domain_mismatch": True,
})

EMAIL = {
    "sender_email": "alice@example.com",
    "sender_name": "Alice",
    "subject": "Reset your password",
    "body": "Click the link below.",
    "urls": ["http://bad.example.com"],
    "attachments": [],
}

# -- the mock itself --

def test_mock_is_an_ai_client():
    assert isinstance(MockAIClient([VALID_REPLY]), ai_client)


def test_mock_returns_its_reply():
    client = MockAIClient([VALID_REPLY])
    assert client.send_request("system", "user") == VALID_REPLY


def test_mock_returns_replies_in_order():
    client = MockAIClient(["first", "second"])
    assert client.send_request("s", "u") == "first"
    assert client.send_request("s", "u") == "second"

def test_mock_raises_an_exception_reply():
    client = MockAIClient([AIConnectionError("timeout")])
    with pytest.raises(AIConnectionError, match="timeout"):
        client.send_request("s", "u")

def test_mock_can_fail_then_succeed():
    client = MockAIClient([AIConnectionError("timeout"), VALID_REPLY])
    with pytest.raises(AIConnectionError):
        client.send_request("s", "u")
    assert client.send_request("s", "u") == VALID_REPLY


def test_mock_records_the_prompts_it_was_sent():
    client = MockAIClient(["a", "b"])
    client.send_request("system 1", "user 1")
    client.send_request("system 2", "user 2")
    assert client.calls == [("system 1", "user 1"), ("system 2", "user 2")]


def test_calls_cannot_be_changed_from_outside():
    client = MockAIClient(["a"])
    client.send_request("system", "user")
    client.calls.append(("fake", "call"))
    assert client.calls == [("system", "user")]
    with pytest.raises(AttributeError):
        client.calls = []

def test_mock_fails_the_test_when_it_runs_out_of_replies():
    client = MockAIClient([])
    with pytest.raises(AssertionError, match="ran out of replies"):
        client.send_request("s", "u")


# -- the AI classes working together, with the mock in place of OpenRouter --

@pytest.fixture
def config():
    return PromptConfig.load_from_yaml_file()


def run_pipeline(client, config):
    """Builds the prompts, asks the client, then parses and validates the reply."""
    builder = PromptBuilder(config)
    content = client.send_request(builder.build_system_prompt(), builder.build_user_prompt(EMAIL))
    response_dict = json.loads(content)
    ResponseValidator.from_config(config).validate(response_dict)
    return response_dict

def test_valid_reply_passes_the_whole_pipeline(config):
    result = run_pipeline(MockAIClient([VALID_REPLY]), config)
    assert result["classification"] == "phishing"
    assert result["threat_level"] == 80

def test_the_built_prompts_are_what_reach_the_client(config):
    client = MockAIClient([VALID_REPLY])
    run_pipeline(client, config)
    system_prompt, user_prompt = client.calls[0]
    assert system_prompt.startswith("You are a phishing detection assistant.")
    assert "Sender email: alice@example.com" in user_prompt

def test_reply_that_breaks_the_schema_is_rejected(config):
    bad_reply = json.dumps({**json.loads(VALID_REPLY), "threat_level": 500})
    with pytest.raises(SchemaValidationError, match="out of range"):
        run_pipeline(MockAIClient([bad_reply]), config)

def test_reply_that_is_not_a_json_object_is_rejected(config): 
    with pytest.raises(SchemaValidationError, match="not a JSON object"):
        run_pipeline(MockAIClient(["[1, 2, 3]"]), config)
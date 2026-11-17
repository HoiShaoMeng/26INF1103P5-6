"""Unit tests for OpenRouterClient: the OpenRouter library is replaced by a fake, so no API key or network is used.

Covers a normal reply, every API failure the client handles (429, 401, 500, timeout, unexpected errors),
an error inside the reply, and replies with an unexpected shape.
"""

import os
import sys
from types import SimpleNamespace
from typing import ClassVar

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ai"))

import open_router_client  # type: ignore
from ai_client import AIClient  # type: ignore
from exceptions import AIConnectionError  # type: ignore
from open_router_client import OpenRouterClient  # type: ignore


# simple stand-ins for the library's error classes (the real ones need a full HTTP response to build)
class FakeTooManyRequests(Exception):
    pass


class FakeUnauthorized(Exception):
    pass


class FakeInternalServer(Exception):
    pass


FAKE_ERRORS = SimpleNamespace(
    TooManyRequestsResponseError=FakeTooManyRequests,
    UnauthorizedResponseError=FakeUnauthorized,
    InternalServerResponseError=FakeInternalServer,
)


# a reply object shaped like the library's: model_dump() gives a dict, error is None unless the API failed
class FakeResponse:
    def __init__(self, data, error=None):
        self._data = data
        self.error = error

    def model_dump(self):
        return self._data


def reply_with(content):
    return FakeResponse({"choices": [{"message": {"content": content}}]})


# replaces the OpenRouter class: records what was sent, then returns the reply or raises the error it was given
class FakeOpenRouter:
    sent: ClassVar[list] = []

    def __init__(self, outcome):
        self._outcome = outcome

    def __call__(self, api_key):
        self.api_key = api_key
        return self

    def __enter__(self):
        self.chat = SimpleNamespace(send=self._send)
        return self

    def __exit__(self, *exc):
        return False

    def _send(self, **request):
        FakeOpenRouter.sent.append(request)
        if isinstance(self._outcome, Exception):
            raise self._outcome
        return self._outcome


@pytest.fixture
def fake_api(monkeypatch):
    FakeOpenRouter.sent = []

    def use(outcome):
        fake = FakeOpenRouter(outcome)
        monkeypatch.setattr(open_router_client, "OpenRouter", fake)
        monkeypatch.setattr(open_router_client, "errors", FAKE_ERRORS)
        return fake

    return use


def make_client():
    return OpenRouterClient("test-key", "test-model:free", 0, 30000)


# --- normal reply ---
def test_returns_the_reply_text(fake_api):
    fake_api(reply_with('{"classification": "phishing"}'))
    assert make_client().send_request("system", "user") == '{"classification": "phishing"}'


def test_sends_the_prompts_and_settings_it_was_given(fake_api):
    fake = fake_api(reply_with("{}"))
    make_client().send_request("the system prompt", "the user prompt")

    request = FakeOpenRouter.sent[0]
    assert fake.api_key == "test-key"
    assert request["model"] == "test-model:free"
    assert request["temperature"] == 0
    assert request["timeout_ms"] == 30000
    assert request["stream"] is False
    assert request["messages"] == [
        {"role": "system", "content": "the system prompt"},
        {"role": "user", "content": "the user prompt"},
    ]


def test_is_an_ai_client_and_reports_its_model():
    client = make_client()
    assert isinstance(client, AIClient)
    assert client.model == "test-model:free"


# --- API failures all become AIConnectionError, so the app shows them and falls back instead of crashing ---
@pytest.mark.parametrize("error, message", [
    (FakeTooManyRequests("slow down"), r"Rate limit hit \(429\)"),
    (FakeUnauthorized("bad key"), r"Invalid API Key \(401\)"),
    (FakeInternalServer("upstream down"), r"server error \(500\)"),
    (TimeoutError("timed out after 30s"), "AI request failed"),
    (ConnectionError("no network"), "AI request failed"),
    (RuntimeError("something unexpected"), "AI request failed"),
])
def test_api_failures_become_ai_connection_errors(fake_api, error, message):
    fake_api(error)
    with pytest.raises(AIConnectionError, match=message):
        make_client().send_request("system", "user")


def test_error_inside_the_reply_is_reported(fake_api):
    fake_api(FakeResponse({}, error="model is unavailable"))
    with pytest.raises(AIConnectionError, match="Openrouter returned an error: model is unavailable"):
        make_client().send_request("system", "user")


# --- replies with an unexpected shape ---
@pytest.mark.parametrize("data", [
    {},
    {"choices": []},
    {"choices": [{}]},
    {"choices": [{"message": {}}]},
    None,
])
def test_reply_with_unexpected_shape_raises(fake_api, data):
    fake_api(FakeResponse(data))
    with pytest.raises(AIConnectionError, match="Unexpected API response structure"):
        make_client().send_request("system", "user")


def test_reply_object_without_model_dump_raises(fake_api):
    fake_api(SimpleNamespace(error=None))
    with pytest.raises(AIConnectionError, match="Unexpected API response structure"):
        make_client().send_request("system", "user")

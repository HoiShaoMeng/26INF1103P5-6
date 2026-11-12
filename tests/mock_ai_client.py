"""MockAIClient: a fake AI client for tests set replies instead of calling OpenRouter."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ai"))


from ai_client import ai_client  # type: ignore


class MockAIClient(ai_client):
    """Stands in for OpenRouterClient in tests, so no API key or network is needed.

    Each call to send_request returns the next reply in the list. A reply that is an
    exception (eg. AIConnectionError("timeout")) is raised instead, so tests can fake
    failtures and retries.
    """

    def __init__(self, replies: list):
        super().__init__()
        self._replies = list(replies)
        self._calls = []

    def send_request(self, system_prompt: str, user_prompt: str) -> str:
        """Records the prompts, then returns (or raises) the next reply"""
        self._calls.append((system_prompt, user_prompt))
        if not self._replies:
            raise AssertionError("MockAiClient ran out of replies: the test called the AI more often than expected.")
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    @property
    def calls(self) -> list[tuple[str, str]]:
        """Returns the (system_prompt, user_prompt) pairs sent so far"""
        return list(self._calls)
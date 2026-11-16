"""ai_manager: runs one AI assessment of a reported email"""
import json

from ai_client import ai_client
from exceptions import MalformedResponseError
from prompt_builder import PromptBuilder
from prompt_config import PromptConfig
from response_validator import ResponseValidator

AI_UNAVAILABLE = "AI_UNAVAILABLE"

class AIManager:
    """Runs one AI assessment: builds the prompts, asks the client, parses and validates the reply"""
    def __init__(self, config: PromptConfig, client: ai_client):
        self._client = client
        self._builder = PromptBuilder(config)
        self._validator = ResponseValidator.from_config(config)

    def assess(self, email: dict) -> dict:
        """Runs one AI assessment of the email"""
        content = self._client.send_request(self._builder.build_system_prompt(), self._builder.build_user_prompt(email))
        response = self._parse(content)
        self._validator.validate(response)
        return response

    @staticmethod
    def unavailable_result() -> dict:
        """Returns a new schema-complete result for when the AI can't produce a valid answer.
            Giving the threat_level a default of 50 is a conservative choice, since it is the midpoint of the allowed range (0-100).
            also falls within the "suspicious" range (50-75) and is a safe default for an unknown threat.
    
        Returns:
            dict: All six output fields with safe defaults, classification
            set to AI_UNAVAILABLE.
        """
        return {
            "classification": AI_UNAVAILABLE,
            "threat_level": 50,
            "tactics_detected": [],
            "suspicious_urls": [],
            "suspicious_attachments": [],
            "sender_domain_mismatch": False,
        }

    @staticmethod
    def _parse(content: str) -> dict:
        """Converts the AI's reply text into a dict.
        
        Raises:
            MalformedResponseError: if the reply is missing or is not valid JSON
        """
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError) as e:
            raise MalformedResponseError(f"AI reply is not valid JSON: {content!r}") from e

    @property
    def client(self):
        return self._client
"""This module contains the ResponseValidator class, which is responsible for validating the response from the AI model"""

from prompt_config import PromptConfig
from validation_rules import (
    BooleanFieldRule,
    ClassificationRule,
    RequireKeysRule,
    StringListRule,
    TacticsDetectedRule,
    ThreatLevelRule,
    ValidationRule,
)
from exceptions import SchemaValidationError


class ResponseValidator:
    def __init__(self, rules: list[ValidationRule]):
        self._rules = list(rules)

    @classmethod
    def from_config(cls, config: PromptConfig) -> "ResponseValidator":
        """Creates a ResponseValidator instance based on the provided PromptConfig.
        Args:
            config (PromptConfig): The configuration object containing validation rules and settings.
        Returns:
            ResponseValidator: An instance of ResponseValidator initialized with the rules derived from the config."""
        output_fields = config.get_output_fields()
        rules = [
            RequireKeysRule(list(output_fields.keys())),
            ClassificationRule(config.get_allowed_classifications()),
            ThreatLevelRule(*config.get_threat_level_range()),
            TacticsDetectedRule(config.get_tactics_vocabulary()),
        ]
        for field_name, field_info in output_fields.items():
            if field_info["type"] == "list":
                rules.append(StringListRule(field_name))
            elif field_info["type"] == "boolean":
                rules.append(BooleanFieldRule(field_name))
        return cls(rules)

    def validate(self, response: dict) -> None:
        """Validates the response from the AI model against the defined validation rules.
        Args:
            response (dict): The response from the AI model to be validated.
        Raises:
            SchemaValidationError: If the response is not a dictionary (JSON object).
            """
        
        if not isinstance(response, dict):
            raise SchemaValidationError("Response is not a JSON object")
        
        for rule in self._rules:
            rule.check(response)
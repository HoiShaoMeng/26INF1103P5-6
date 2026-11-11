"""Validation rules for ai responses."""

from abc import ABC, abstractmethod


class ValidationRule(ABC):
    """Base class for ai validation rules."""

    @abstractmethod
    def check(self, response: dict) -> None:
        pass

    # will add validation of the exception error when its ready

    def _fail(self, message: str) -> None:
        raise ValueError(message)

class RequireKeysRule(ValidationRule):
    """Validation rule that checks if certain keys are present in the response."""

    def __init__(self, required_keys: list[str]):
        self._required_keys = required_keys

    def check(self, response: dict) -> None:
        missing_keys = [key for key in self._required_keys if key not in response]
        if missing_keys:
            self._fail(f"Missing required keys: {', '.join(missing_keys)}")

class ClassificationRule(ValidationRule):
    """Validation rule that checks if the classification is one of the allowed classifications."""

    def __init__(self, allowed_classifications: list[str]):
        self._allowed_classifications = allowed_classifications

    def check(self, response: dict) -> None:
        classification = response.get("classification")
        if classification not in self._allowed_classifications:
            self._fail(f"Invalid classification: {classification}. Allowed classifications are: {', '.join(self._allowed_classifications)}")

class ThreatLevelRule(ValidationRule):
    """Validation rule that checks if the threat level is within the allowed range."""

    def __init__(self, min_level: int, max_level: int):
        self._min_level = min_level
        self._max_level = max_level

    def check(self, response: dict) -> None:
        threat_level = response.get("threat_level")
        if isinstance(threat_level, bool) or not isinstance(threat_level, (int)):
            self._fail(f"Threat level must be an integer`. Got: {type(threat_level).__name__}")
        if not (self._min_level <= threat_level <= self._max_level):
            self._fail(f"Threat level {threat_level} is out of range [{self._min_level}, {self._max_level}]")

class StringListRule(ValidationRule):
    """Validation rule that checks if a field is a list of strings."""

    def __init__(self, field_name: str):
        self._field_name = field_name

    def check(self, response: dict) -> None:
        value = response.get(self._field_name)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            self._fail(f"{self._field_name} must be a list of strings. Got: {value}")

class TacticsDetectedRule(ValidationRule):
    """Validation rule that checks if the tactics_detected field is a list of allowed tactics."""

    def __init__(self, allowed_tactics: list[str]):
        self._allowed_tactics = allowed_tactics

    def check(self, response: dict) -> None:
        tactics_detected = response.get("tactics_detected")
        if not isinstance(tactics_detected, list) or not all(isinstance(tactic, str) for tactic in tactics_detected):
            self._fail(f"tactics_detected must be a list of strings. Got: {tactics_detected}")
        if len(tactics_detected) != len(set(tactics_detected)):
            self._fail(f"tactics_detected contains duplicate values: {tactics_detected}")
        invalid_tactics = [tactic for tactic in tactics_detected if tactic not in self._allowed_tactics]
        if invalid_tactics:
            self._fail(f"Invalid tactics detected: {', '.join(invalid_tactics)}. Allowed tactics are: {', '.join(self._allowed_tactics)}")

class BooleanFieldRule(ValidationRule):
    """Validation rule that checks if a field is a boolean."""

    def __init__(self, field_name: str):
        self._field_name = field_name

    def check(self, response: dict) -> None:
        value = response.get(self._field_name)
        if not isinstance(value, bool):
            self._fail(f"{self._field_name} must be a boolean. Got: {type(value).__name__}")
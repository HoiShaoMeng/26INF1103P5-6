"""Unit tests for ResponseValidator and the validation rules: responses are built in the test, so no API is needed."""

import os
import sys

import pytest

# adds the src/ai folder to the path so we can import response_validator.py for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ai"))

from prompt_config import PromptConfig  # type: ignore
from response_validator import ResponseValidator  # type: ignore
from validation_rules import (  # type: ignore
    RequireKeysRule,
    ThreatLevelRule,
    ValidationRule,
)

# Temporary: the rules raise ValueError until the team's SchemaValidationError is ready.
# When it is, replace this line with an import of SchemaValidationError
SchemaValidationError = ValueError

@pytest.fixture
def config():
    return PromptConfig(
        model = "test-model",
        temperature = 0,
        allowed_classifications=["phishing", "spear-phishing", "spam", "benign"],
        tactics_vocabulary=["impersonation", "urgency_pressure", "credential_harvesting"],
        threat_level_range=[0, 100],
        output_fields={
            "classification": {"type": "string", "description": "one of allowed_classifications"},
            "threat_level": {"type": "integer", "description": "0-100"},
            "tactics_detected": {"type": "list", "description": "only from tactics_vocabulary"},
            "suspicious_urls": {"type": "list", "description": "[] if none"},
            "suspicious_attachments": {"type": "list", "description": "[] if none"},
            "sender_domain_mismatch": {"type": "boolean", "description": "boolean"}
        },
        rules=["Output JSON only"]
    )

@pytest.fixture
def validator(config):
    return ResponseValidator.from_config(config)

@pytest.fixture
def response():
    return {
        "classification": "phishing",
        "threat_level": 80,
        "tactics_detected": ["impersonation", "urgency_pressure"],
        "suspicious_urls": ["http://bad.example.com"],
        "suspicious_attachments": [],
        "sender_domain_mismatch": True
    }


# -- valid response -- 

def test_valid_response_passes(validator, response):
    validator.validate(response)

def test_empty_tactics_list_passes(validator, response):
    response["tactics_detected"] = []
    validator.validate(response)

@pytest.mark.parametrize("threat_level", [0, 100])
def test_threat_level_at_range_limits_passes(validator, response, threat_level):
    response["threat_level"] = threat_level
    validator.validate(response)

def test_validator_builds_from_real_config_file(response):
    config = PromptConfig.load_from_yaml_file()
    validator = ResponseValidator.from_config(config)
    validator.validate(response)  # should not raise an exception if the response is valid

# -- Invalid response --

@pytest.mark.parametrize("not_a_dict", [[], "phishing", None, 42])
def test_non_dict_response_rejected(validator, not_a_dict):
    with pytest.raises(SchemaValidationError, match="not a JSON object"):
        validator.validate(not_a_dict)

def test_missing_key_is_rejected_and_named(validator, response):
    del response["suspicious_urls"]
    with pytest.raises(SchemaValidationError, match="Missing required keys: suspicious_urls"):
        validator.validate(response)

def test_unknown_classification_is_rejected(validator, response):
    response["classification"] = "scam"
    with pytest.raises(SchemaValidationError, match="Invalid classification: scam"):
        validator.validate(response)

@pytest.mark.parametrize("threat_level", [True, 55.5, "80", None])
def test_threat_level_that_is_not_an_integer_is_rejected(validator, response, threat_level):
    response["threat_level"] = threat_level
    with pytest.raises(SchemaValidationError, match="Threat level must be an integer"):
        validator.validate(response)

@pytest.mark.parametrize("threat_level", [-1, 101])
def test_threat_level_out_of_range_is_rejected(validator, response, threat_level):
    response["threat_level"] = threat_level
    with pytest.raises(SchemaValidationError, match=f"Threat level {threat_level} is out of range"):
        validator.validate(response)

def test_duplicate_tactics_are_rejected(validator, response):
    response["tactics_detected"] = ["impersonation", "impersonation"]
    with pytest.raises(SchemaValidationError, match="duplicate"):
        validator.validate(response)

def test_unknown_tactics_are_rejected(validator, response):
    response["tactics_detected"] = ["mind control"]
    with pytest.raises(SchemaValidationError, match="Invalid tactics detected: mind control"):
        validator.validate(response)

@pytest.mark.parametrize("value", ["http://bad.example.com", [1,2], None])
def test_list_fields_that_are_not_list_of_strings_are_rejected(validator, response, value):
    response["suspicious_urls"] = value
    with pytest.raises(SchemaValidationError, match="suspicious_urls must be a list of strings"):
        validator.validate(response)

@pytest.mark.parametrize("value", ["yes", 1, None])
def test_boolean_field_that_is_not_boolean_is_rejected(validator, response, value):
    response["sender_domain_mismatch"] = value
    with pytest.raises(SchemaValidationError, match="sender_domain_mismatch must be a boolean"):
        validator.validate(response)

# -- class design -- 

def test_validation_rule_cannot_be_created_directly():
    with pytest.raises(TypeError):
        ValidationRule()

def test_rule_without_check_cannot_be_created():
    class IncompleteRule(ValidationRule):
        pass

    with pytest.raises(TypeError):
        IncompleteRule()

def test_validator_only_runs_the_rules_it_is_given():
    validator = ResponseValidator([ThreatLevelRule(0, 100)])
    validator.validate({"threat_level": 50})  # should pass
    with pytest.raises(SchemaValidationError):
        validator.validate({"threat_level": 150})  # should fail

def test_validator_stops_at_the_first_failing_rule():
    validator = ResponseValidator([RequireKeysRule(["classification"]), ThreatLevelRule(0, 100)])
    with pytest.raises(SchemaValidationError, match="Missing required keys"):
        validator.validate({"threat_level": 500})
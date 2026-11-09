"""prompt_config: loads and checks the AI prompt configuration from prompt_config.yaml"""

import copy
import os

import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "prompt_config.yaml")


class PromptConfig:
    """Represents the configuration for the AI prompt, loaded from a YAML file."""
    def __init__(self, model: str, temperature: float, allowed_classifications: list[str], threat_level_range: tuple[int, int], tactics_vocabulary: list[str], output_fields: dict, rules: list[str]):
        self._model = model
        self._temperature = temperature
        self._allowed_classifications = allowed_classifications
        self._threat_level_range = tuple(threat_level_range)
        self._tactics_vocabulary = tactics_vocabulary
        self._output_fields = output_fields
        self._rules = rules

    @classmethod
    def load_from_yaml_file(cls, file_path: str = CONFIG_PATH) -> 'PromptConfig':
        with open(file_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
            requirements = config_data.get('requirements', {})

        # will add validation of the config data here when configerror is ready
        
        return cls(
            model=config_data.get('model'),
            temperature=config_data.get('temperature', 0),
            allowed_classifications=requirements.get('allowed_classifications'),
            threat_level_range=requirements.get('threat_level_range'),
            tactics_vocabulary=requirements.get('tactics_vocabulary'),
            output_fields=requirements.get('output_fields'),
            rules=requirements.get('rules')
        )

    def get_model(self) -> str:
        return self._model

    def get_temperature(self) -> float:
        return self._temperature

    def get_allowed_classifications(self) -> list[str]:
        return list(self._allowed_classifications)

    def get_threat_level_range(self) -> tuple[int, int]:
        return self._threat_level_range

    def get_tactics_vocabulary(self) -> list[str]:
        return list(self._tactics_vocabulary)

    def get_output_fields(self) -> dict:
        return copy.deepcopy(self._output_fields)

    def get_rules(self) -> list[str]:
        return list(self._rules)
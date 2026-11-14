import json
import os
import sys

import yaml
from ai_client import ai_client
from exceptions import MalformedResponseError, SchemaValidationError
from openrouter import OpenRouter, errors
from prompt_builder import PromptBuilder
from prompt_config import PromptConfig
from response_validator import ResponseValidator

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "io"))
import io_manager

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "prompt_config.yaml")


AI_UNAVAILABLE = "AI_UNAVAILABLE"

def build_unavailable_result() -> dict:
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

def load_prompt_config(path=CONFIG_PATH) -> dict | None:
    """Loads the prompt configuration from a YAML file.

    Args:
        path (str): Path to the YAML config file.

    Returns:
        dict: The parsed config, or None if the file is missing or invalid.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        io_manager.display_error("Prompt config", f"File not found: {path}")
        return None
    except yaml.YAMLError as e:
        io_manager.display_error("Prompt config", f"Prompt config is not valid YAML: {e}")
        return None

def build_system_prompt(config: dict) -> str:
    """Builds the system prompt string from the config.

    Args:
        config (dict): The parsed prompt config.

    Returns:
        str: The system prompt string.
    """
    req = config["requirements"]
    output_field_rules = req["output_fields"]
    system_prompt = ("You are a phishing detection assistant. "
                    "Respond ONLY with valid JSON matching this schema:{ "
                    f'"classification": {req["allowed_classifications"]}, '
                    f'"tactics_detected": {req["tactics_vocabulary"]}, '
                    f'"threat_level": {req["threat_level_range"]},'
                    f'"output_fields_rules": {output_field_rules},'
                    f'"rule": {req["rules"]},'
                    '}')
    return system_prompt

def build_user_prompt(email_data: dict) -> str:
    """Builds the user prompt string from the email data.

    Args:
        email_data (dict): The email data with keys such as 'sender_email',
            'sender_name', 'subject', 'body', 'urls', and 'attachments'.
            Attachments must be dictionaries containing a 'filename' key and
            may also contain an 'extension' key.

    Returns:
        str: The user prompt string.
    """
    attachment_names = [
        attachment["filename"]
        for attachment in email_data.get("attachments", [])
    ]
    return (
        f"Sender email: {email_data['sender_email']}\n"
        f"Sender name: {email_data['sender_name']}\n"
        f"Subject: {email_data['subject']}\n"
        f"Body: {email_data['body']}\n"
        f"URLs: {', '.join(email_data.get('urls', [])) or 'none'}\n"
        f"Attachments: {', '.join(attachment_names) or 'none'}\n"
    )

def parse_response_content(content_str: str) -> dict | None:
    """Converts the model's JSON text into a Python dict.

    Args:
        content_str (str): The content text returned by receive_response().

    Returns:
        dict: The model's assessment (e.g. classification, threat_level),
        or None if content_str is None or not valid JSON.
    """
    try:
        return json.loads(content_str)
    except (json.JSONDecodeError, TypeError):
        io_manager.display_error("Response", f"Failed to parse content string as JSON: {content_str}")
        return None

def receive_response(api_response) -> str | None:
    """Extracts the model's reply text from the OpenRouter SDK response.

    Args:
        api_response: The response object returned by open_router.chat.send()
            (a Pydantic model, not a dict).

    Returns:
        str: The raw content text written by the model (expected to be JSON text),
        or None if the response is missing or not shaped as expected.
    """
    try:
        response = api_response.model_dump()
        message = response["choices"][0]["message"]
        content_body = message["content"]
        return content_body

    except (KeyError, IndexError, TypeError, AttributeError):
        io_manager.display_error("API Response", f"Unexpected API response structure: {api_response}")
        return None

def send_request(system: str, user: str, config: dict) -> dict | None:
    """Sends a request to the OpenRouter API through the OpenRouter SDK.

    Args:
        system (str): The system prompt describing the format the AI must follow.
        user (str): The reported email, formatted as the user prompt.
        config (dict): The loaded prompt config; config["model"] selects the AI model.

    Returns:
        The OpenRouter response object, or None if the request failed.
    """
    try:
        model = config["model"]
        temperature = config["temperature"]
    except KeyError as e:
        io_manager.display_error("AI request", f"Missing key in config: {e}")
        return None

    with OpenRouter(
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
    ) as open_router:
        try:
            res = open_router.chat.send(
                model= model,
                messages=[
                    {"role": "system", "content": system}, {"role": "user", "content": user}
                ],
                stream=False,
                temperature=temperature,
                timeout_ms=30000,  # 30 seconds
            )
            error = getattr(res, "error", None)
            if error:
                io_manager.display_error("AI request", f"OpenRouter returned an error: {error}")
                return None

        except errors.TooManyRequestsResponseError as e:
            io_manager.display_error("AI request",f"Rate limit hit (429): {e}")
            return None
        except errors.UnauthorizedResponseError as e:
            io_manager.display_error("AI request",f"Invalid API key (401): {e}")
            return None
        except errors.InternalServerResponseError as e:
            io_manager.display_error("AI request",f"OpenRouter or upstream server error (500): {e}")
            return None
        except Exception as e: # noqa: BLE001 keep the batch running if OpenRouter returns an unexpected payload or transient failure
            # OpenRouter is an external service and may raise shapes we did not anticipate
            # (e.g. malformed JSON, unexpected response objects, or upstream runtime errors).
            # We do not want one failed AI call to crash the whole workflow; the caller
            # handles None by returning a safe "AI unavailable" fallback.
            io_manager.display_error("AI request",f"{e}")
            return None
    return res

def ai_workflow(system_prompt: str, user_prompt: str, config: dict) -> dict:
    """Runs the full process from sending request to returning a formatted dictionary

    Args:
        system_prompt: The structure that the AI is required to follow

        user_prompt: The input given by the user

        config: The configuration that contains the rules and requirements for the AI to follow
    
    Returns:
        response_dict: Dictionary containing parsed content only
    """
    response = send_request(system_prompt, user_prompt, config)
    if response is None:
        return build_unavailable_result()
    
    response_content = receive_response(response)
    response_dict = parse_response_content(response_content)

    validator = ResponseValidator.from_config(PromptConfig.from_dict(config))
    try:
        validator.validate(response_dict)

    except SchemaValidationError as e:
        io_manager.display_error("Validation", str(e))
        return build_unavailable_result()

    return response_dict

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
import json
import os
import sys

import yaml
from openrouter import OpenRouter, errors

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

def is_response_dictionary(response_dict: dict) -> bool:
    """Checks whether the model's response is a dictionary.
    Args:
        response_dict: The parsed JSON response from the model.

    Returns:
        bool: True if the response is a dictionary, False otherwise.
    """
    if not isinstance(response_dict, dict):
        io_manager.display_error("Response", "Response is not a dictionary.")
        return False
    return True

def is_allowed_classification(classification: str, allowed_classifications: list) -> bool:
    """Checks whether the classification is in the allowed classifications.

    Args:
        classification (str): The classification returned by the model.
        allowed_classifications (list): The list of allowed classifications.
    Returns:
        bool: True if the classification is allowed, False otherwise.
    """
    return classification in allowed_classifications

def has_required_keys(response_dict: dict, required_keys: list) -> bool:
    """Checks whether the model's response contains all required keys.
    Args:
        response_dict: The parsed JSON response from the model.
        required_keys (list): A list of required keys.

    Returns:
        bool: True if all required keys are present, False otherwise.
    """
    for key in required_keys:
        if key not in response_dict:
            io_manager.display_error("Validation", f"Missing required key in response: {key}")
            return False
    return True

def has_valid_threat_level(response_dict: dict, threat_level_range: list) -> bool:
    """Checks whether the response threat level is an integer and in range.
    Args:
        response_dict: The parsed JSON response from the model.
        threat_level_range (list): A list containing the minimum and maximum allowed threat levels.

    Returns:
        bool: True if the threat level is valid, False otherwise.
    """
    if "threat_level" not in response_dict:
        return True

    threat_level = response_dict["threat_level"]
    if isinstance(threat_level, bool) or not isinstance(threat_level, int):
        io_manager.display_error("Validation", "Threat level is not an integer.")
        return False
    if threat_level < threat_level_range[0] or threat_level > threat_level_range[1]:
        io_manager.display_error("Validation", "Threat level is out of the allowed range.")
        return False
    return True

def has_lists_of_strings(response_dict: dict, list_keys: list) -> bool:
    """Checks whether the specified keys in the response are lists of strings.

    Args:
        response_dict: The parsed JSON response from the model.
        list_keys (list): A list of keys that should contain lists of strings.
    Returns:
        bool: True if all specified keys contain lists of strings, False otherwise.
    """
    for key in list_keys:
        if key not in response_dict:
            io_manager.display_error("Validation", f"Key not found in response: {key}")
            return False
        if not isinstance(response_dict[key], list):
            io_manager.display_error("Validation", f"Value for key {key} is not a list.")
            return False
        for item in response_dict[key]:
            if not isinstance(item, str):
                io_manager.display_error("Validation", f"Item in list for key {key} is not a string.")
                return False
    return True

def has_valid_tactics(response_dict: dict, tactics_vocabulary: list) -> bool:
    """Checks that tactics are allowed and are not duplicated.

    Args:
        response_dict: The parsed JSON response from the model.
        tactics_vocabulary: The list of tactics allowed by the configuration.

    Returns:
        bool: True if all tactics are allowed and unique, False otherwise.
    """
    tactics = response_dict["tactics_detected"]
    if len(tactics) != len(set(tactics)):
        io_manager.display_error("Validation", "Tactics detected must not contain duplicates.")
        return False
    if any(tactic not in tactics_vocabulary for tactic in tactics):
        io_manager.display_error("Validation", "Tactics detected contains an unknown tactic.")
        return False
    return True

def is_boolean(value: object) -> bool:
    """Checks whether the value is a boolean.

    Args:
        value: The value to check.

    Returns:
        bool: True if the value is a boolean, False otherwise.
    """
    return isinstance(value, bool)

def validate_schema(response_dict: dict, config: dict) -> bool:
    """Validates the model's response against the expected schema defined in the prompt configuration.

    Args:
        response_dict (dict): The parsed JSON response from the model.
        config (dict): The prompt configuration containing the expected schema.

    Returns:
        bool: True if valid, False otherwise.
    """
    req = config["requirements"]
    required_keys = req["output_fields"].keys()
    if not is_response_dictionary(response_dict):
        return False

    if not is_allowed_classification(response_dict.get("classification"), req["allowed_classifications"]):
        return False

    if not has_required_keys(response_dict, required_keys):
        return False

    threat_level_range = req["threat_level_range"]
    if not has_valid_threat_level(response_dict, threat_level_range):
        return False

    field_types = {
        key: field["type"] for key, field in req["output_fields"].items()
    }
    list_keys = [key for key, value in field_types.items() if value == "list"]
    if not has_lists_of_strings(response_dict, list_keys):
        return False

    if not has_valid_tactics(response_dict, req["tactics_vocabulary"]):
        return False

    boolean_keys = [key for key, value in field_types.items() if value == "boolean"]
    for key in boolean_keys:
        if not is_boolean(response_dict.get(key)):
            io_manager.display_error("Validation", f"Value for key {key} is not a boolean.")
            return False

    # Additional validation logic can be added here (e.g., type checks, value ranges)
    return True

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

def send_request(system: str, user: str, config: dict) -> any | None:
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
    if validate_schema(response_dict, config):
        
        return response_dict
    else:
        return build_unavailable_result()
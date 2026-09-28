import json
import os
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "prompt_config.yaml")

SAMPLE_EMAILS = {
    # Expected: spear-phishing, threat_level 80-95
    "spear_phishing_ceo": {
        "sender_email": "john.tan@yourcompany-support.com",
        "sender_name": "John Tan (CEO)",
        "subject": "Quick favor - urgent wire transfer",
        "body": (
            "Hi Sarah,\n\n"
            "I'm stuck in a meeting and can't call. Can you process an urgent wire "
            "transfer of $8,500 to our new vendor today? I'll send the account "
            "details shortly. Please keep this between us for now, it's time "
            "sensitive.\n\n"
            "Thanks,\nJohn"
        ),
        "urls": [],
        "attachments": [],
    },

}

def load_prompt_config(path=CONFIG_PATH):
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
        print(f"Prompt config not found: {path}")
        return None
    except yaml.YAMLError as e:
        print(f"Prompt config is not valid YAML: {e}")
        return None

def build_system_prompt(config):
    """Builds the system prompt string from the config.

    Args:
        config (dict): The parsed prompt config.

    Returns:
        str: The system prompt string.
    """
    req = config["requirements"]
    output_field_rules = req["output_fields"]
    print(req)
    print(output_field_rules)
    system_prompt = ("You are a phishing detection assistant. "
                    "Respond ONLY with valid JSON matching this schema:{ "
                    f'"classification": {req["allowed_classifications"]}, '
                    f'"tactics_used": {req["tactics_vocabulary"]}, '
                    f'"threat_level": {req["threat_level_range"]},'
                    f'"output_fields_rules": {output_field_rules},'
                    f'"rule": {req["rules"]},'
                    '}')
    return system_prompt

def build_user_prompt(email_data=SAMPLE_EMAILS["spear_phishing_ceo"]):
    """Builds the user prompt string from the email data.

    Args:
        email_data (dict): The email data with keys like 'sender_email', 'sender_name', etc.

    Returns:
        str: The user prompt string.
    """
    return (
        f"Sender email: {email_data['sender_email']}\n"
        f"Sender name: {email_data['sender_name']}\n"
        f"Subject: {email_data['subject']}\n"
        f"Body: {email_data['body']}\n"
        f"URLs: {', '.join(email_data.get('urls', [])) or 'none'}\n"
        f"Attachments: {', '.join(email_data.get('attachments', [])) or 'none'}"
    )


def parse_response_content(content_str):
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
        print(f"Failed to parse content string as JSON: {content_str}")
        return None

def receive_response(api_response):
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
        print(f"Unexpected API response structure: {api_response}")
        return None


import json
import os
import yaml
from openrouter import OpenRouter

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
 
    # Expected: phishing, threat_level 80-95 (malicious attachment)
    "phishing_fake_invoice": {
        "sender_email": "billing@acc0unts-payable.net",
        "sender_name": "Accounts Payable",
        "subject": "Overdue invoice #INV-20931 - final notice",
        "body": (
            "Hello,\n\n"
            "Your payment for the attached invoice is now 30 days overdue. Please "
            "open the attached file and enable macros to view the full breakdown. "
            "Failure to pay within 48 hours will result in legal action.\n\n"
            "Regards,\nAccounts Payable"
        ),
        "urls": [],
        "attachments": [
            {"filename": "INV-20931.pdf.exe", "extension": "exe"},
            {"filename": "payment_details.docm", "extension": "docm"},
        ],
    },

    # Expected: phishing, threat_level 50-75 (IT impersonation, softer tone)
    "borderline_it_mailbox": {
        "sender_email": "it-helpdesk@yourcompany-mail.org",
        "sender_name": "IT Helpdesk",
        "subject": "Mailbox storage almost full",
        "body": (
            "Hi,\n\n"
            "Your mailbox has reached 95% of its storage limit. To avoid losing "
            "incoming emails, please log in to the portal below to increase your "
            "quota.\n\n"
            "IT Helpdesk"
        ),
        "urls": ["https://yourcompany-mail.org/quota-upgrade"],
        "attachments": [],
    },

    # Expected: spam, threat_level 15-35
    "spam_newsletter": {
        "sender_email": "news@crypto-daily-insider.info",
        "sender_name": "Crypto Daily Insider",
        "subject": "This coin could 100x next week",
        "body": (
            "Our analysts have found the next big thing in crypto. Subscribers "
            "who got in early last month saw huge returns. Read the full report "
            "on our website."
        ),
        "urls": ["http://crypto-daily-insider.info/report"],
        "attachments": [],
    },
   
    # Expected: benign, threat_level 0-15 (false-positive test)
    "benign_security_alert": {
        "sender_email": "no-reply@accounts.google.com",
        "sender_name": "Google",
        "subject": "Security alert: New sign-in from Windows device",
        "body": (
            "We noticed a new sign-in to your Google Account on a Windows device. "
            "If this was you, no action is needed. If not, we recommend securing "
            "your account."
        ),
        "urls": ["https://myaccount.google.com/notifications"],
        "attachments": [],
    },
 
    # Expected: benign, threat_level 0-15 (legit attachment from internal sender)
    "benign_meeting_notes": {
        "sender_email": "mei.lin@yourcompany.com",
        "sender_name": "Mei Lin",
        "subject": "Notes from Monday's project meeting",
        "body": (
            "Hi all,\n\n"
            "Attached are the notes from Monday's meeting. Please review the action "
            "items assigned to you before our next check-in on Thursday.\n\n"
            "Mei Lin"
        ),
        "urls": [],
        "attachments": [
            {"filename": "meeting_notes_2026-09-28.pdf", "extension": "pdf"},
        ],
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
                    f'"tactics_detected": {req["tactics_vocabulary"]}, '
                    f'"threat_level": {req["threat_level_range"]},'
                    f'"output_fields_rules": {output_field_rules},'
                    f'"rule": {req["rules"]},'
                    '}')
    return system_prompt

def build_user_prompt(email_data=SAMPLE_EMAILS["spear_phishing_ceo"]):
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

def is_response_dictionary(response_dict):
    """Checks whether the model's response is a dictionary.
    Args:
        response_dict: The parsed JSON response from the model.

    Returns:
        bool: True if the response is a dictionary, False otherwise.
    """
    if not isinstance(response_dict, dict):
        print("Response is not a dictionary.")
        return False
    return True

def is_allowed_classification(classification, allowed_classifications):
    """Checks whether the classification is in the allowed classifications.

    Args:
        classification (str): The classification returned by the model.
        allowed_classifications (list): The list of allowed classifications.
    Returns:
        bool: True if the classification is allowed, False otherwise.
    """
    return classification in allowed_classifications

def has_required_keys(response_dict, required_keys):
    """Checks whether the model's response contains all required keys.
    Args:
        response_dict: The parsed JSON response from the model.
        required_keys (list): A list of required keys.

    Returns:
        bool: True if all required keys are present, False otherwise.
    """
    for key in required_keys:
        if key not in response_dict:
            print(f"Missing required key in response: {key}")
            return False
    return True

def has_valid_threat_level(response_dict, threat_level_range):
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
        print("Threat level is not an integer.")
        return False
    if threat_level < threat_level_range[0] or threat_level > threat_level_range[1]:
        print("Threat level is out of the allowed range.")
        return False
    return True

def has_lists_of_strings(response_dict, list_keys):
    """Checks whether the specified keys in the response are lists of strings.

    Args:
        response_dict: The parsed JSON response from the model.
        list_keys (list): A list of keys that should contain lists of strings.
    Returns:
        bool: True if all specified keys contain lists of strings, False otherwise.
    """
    for key in list_keys:
        if key not in response_dict:
            print(f"Key not found in response: {key}")
            return False
        if not isinstance(response_dict[key], list):
            print(f"Value for key {key} is not a list.")
            return False
        for item in response_dict[key]:
            if not isinstance(item, str):
                print(f"Item in list for key {key} is not a string.")
                return False
    return True

def has_valid_tactics(response_dict, tactics_vocabulary):
    """Checks that tactics are allowed and are not duplicated.

    Args:
        response_dict: The parsed JSON response from the model.
        tactics_vocabulary: The list of tactics allowed by the configuration.

    Returns:
        bool: True if all tactics are allowed and unique, False otherwise.
    """
    tactics = response_dict["tactics_detected"]
    if len(tactics) != len(set(tactics)):
        print("Tactics detected must not contain duplicates.")
        return False
    if any(tactic not in tactics_vocabulary for tactic in tactics):
        print("Tactics detected contains an unknown tactic.")
        return False
    return True

def is_boolean(value):
    """Checks whether the value is a boolean.

    Args:
        value: The value to check.

    Returns:
        bool: True if the value is a boolean, False otherwise.
    """
    return isinstance(value, bool)

def validate_schema(response_dict, config):
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
            print(f"Value for key {key} is not a boolean.")
            return False

    # Additional validation logic can be added here (e.g., type checks, value ranges)
    return True

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

system_prompt = build_system_prompt(load_prompt_config())
user_prompt = build_user_prompt()

def send_request(system=system_prompt, user=user_prompt):
    with OpenRouter(
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
    ) as open_router:
        res = open_router.chat.send(
            model= "dots-studio/dots-3-note-preview:free",
            messages=[
                {"role": "system", "content": system}, {"role": "user", "content": user}
            ],
            stream=False,
        )
    return res

print(receive_response(send_request()))


"""
io_manager.py

Input and output layer for the Phishing / Suspicious Email Triage Assistant.

Responsibilities:
- Collect user input using input()
- Validate required fields
- Validate input types and basic ranges
- Re-prompt users when invalid input is entered
- Return clean, validated data to the AI layer
- Display all user-facing messages

Architecture:
    io_manager.py
        ↓
    ai_manager.py
        ↓
    logic_manager.py
        ↓
    data_manager.py

This module does NOT:
- Call the AI API
- Perform phishing classification
- Apply business rules
- Save data to files
"""


# =========================================================
# DISPLAY FUNCTIONS
# =========================================================

def display_welcome():
    """Display the application welcome message."""

    print("\n==============================================")
    print("       PHISHING TRIAGE ASSISTANT")
    print("==============================================")
    print("Analyse suspicious emails for initial triage.")
    print("Please provide the requested email information.")
    print("==============================================\n")


def display_error(message):
    """Display an error message to the user."""

    print(f"[ERROR] {message}")


def display_message(message):
    """Display a normal message to the user."""

    print(message)


def display_success(message):
    """Display a success message to the user."""

    print(f"[OK] {message}")


# =========================================================
# INPUT FUNCTIONS
# =========================================================

def get_sender_email():
    """
    Collect and validate the sender email address.

    Expected type:
        str

    Required:
        Yes

    Returns:
        str: Validated sender email address.
    """

    while True:
        value = input("Enter sender email: ").strip()

        if not value:
            display_error("Sender email is required.")
            continue

        if "@" not in value:
            display_error("Please enter a valid email address.")
            continue

        username, domain = value.split("@", 1)

        if not username or not domain:
            display_error("Please enter a valid email address.")
            continue

        if "." not in domain:
            display_error("Please enter a valid email address.")
            continue

        return value


def get_subject():
    """
    Collect and validate the email subject.

    Expected type:
        str

    Required:
        Yes

    Returns:
        str: Validated email subject.
    """

    while True:
        value = input("Enter email subject: ").strip()

        if not value:
            display_error("Email subject is required.")
            continue

        return value


def get_email_body():
    """
    Collect and validate the email body.

    Expected type:
        str

    Required:
        Yes

    Returns:
        str: Validated email body.
    """

    while True:
        value = input("Enter email body: ").strip()

        if not value:
            display_error("Email body is required.")
            continue

        return value


def get_urgency():
    """
    Collect and validate the user's urgency level.

    Expected type:
        int

    Valid range:
        1 - 5

    Returns:
        int: Validated urgency level.
    """

    while True:
        value = input(
            "Enter urgency level (1-5): "
        ).strip()

        try:
            urgency = int(value)
        except ValueError:
            display_error("Urgency must be a whole number from 1 to 5.")
            continue

        if urgency < 1 or urgency > 5:
            display_error("Urgency must be between 1 and 5.")
            continue

        return urgency


# =========================================================
# VALIDATION FUNCTIONS
# =========================================================

def validate_sender_email(email):
    """
    Validate an email address.

    Args:
        email (str): Email address to validate.

    Returns:
        bool: True if valid, otherwise False.
    """

    if not isinstance(email, str):
        return False

    email = email.strip()

    if not email:
        return False

    if "@" not in email:
        return False

    username, domain = email.split("@", 1)

    if not username or not domain:
        return False

    if "." not in domain:
        return False

    return True


def validate_required_text(value):
    """
    Validate a required text field.

    Args:
        value (str): Value to validate.

    Returns:
        bool: True if valid, otherwise False.
    """

    if not isinstance(value, str):
        return False

    if not value.strip():
        return False

    return True


def validate_urgency(value):
    """
    Validate urgency level.

    Args:
        value (int): Urgency value.

    Returns:
        bool: True if value is an integer from 1 to 5.
    """

    if not isinstance(value, int):
        return False

    return 1 <= value <= 5


# =========================================================
# STRUCTURED INPUT COLLECTION
# =========================================================

def collect_email_data():
    """
    Collect all required email information.

    Returns:
        dict: Clean and validated email data.

    Example:
        {
            "sender": "example@company.com",
            "subject": "Urgent account verification",
            "body": "Your account requires verification.",
            "urgency": 3
        }
    """

    sender = get_sender_email()
    subject = get_subject()
    body = get_email_body()
    urgency = get_urgency()

    # Final validation before data leaves IO layer.
    if not validate_sender_email(sender):
        display_error("Invalid sender email.")
        return collect_email_data()

    if not validate_required_text(subject):
        display_error("Invalid email subject.")
        return collect_email_data()

    if not validate_required_text(body):
        display_error("Invalid email body.")
        return collect_email_data()

    if not validate_urgency(urgency):
        display_error("Invalid urgency level.")
        return collect_email_data()

    return {
        "sender": sender,
        "subject": subject,
        "body": body,
        "urgency": urgency
    }


# =========================================================
# RESULT DISPLAY
# =========================================================

def display_triage_result(result):
    """
    Display the result returned by the processing pipeline.

    Args:
        result (dict): Processed triage result.
    """

    print("\n==============================================")
    print("              TRIAGE RESULT")
    print("==============================================")

    if not isinstance(result, dict):
        display_error("Invalid result received.")
        return

    print(f"Classification : {result.get('classification', 'Unknown')}")
    print(f"Severity       : {result.get('severity', 'Unknown')}")
    print(f"Confidence     : {result.get('confidence', 'Unknown')}")
    print(f"Reason         : {result.get('reason', 'Not provided')}")

    print("==============================================\n")


# =========================================================
# MENU
# =========================================================

def display_menu():
    """Display the main application menu."""

    print("\n========== MAIN MENU ==========")
    print("1. Analyse suspicious email")
    print("2. Exit")
    print("===============================")


def get_menu_choice():
    """
    Get and validate the user's menu choice.

    Expected type:
        int

    Valid range:
        1 - 2

    Returns:
        int: Valid menu choice.
    """

    while True:
        value = input("Enter your choice (1-2): ").strip()

        try:
            choice = int(value)
        except ValueError:
            display_error("Please enter a number.")
            continue

        if choice < 1 or choice > 2:
            display_error("Please choose 1 or 2.")
            continue

        return choice

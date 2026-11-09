"""prompt_builder: builds the system and user prompts for the AI model based on the prompt configuration and email data."""

from prompt_config import PromptConfig


class PromptBuilder:
    """Builds the system and user prompts for the AI model based on the prompt configuration and email data."""
    def __init__(self, config: PromptConfig):
        self._config = config

    def build_system_prompt(self) -> str:
        """Builds the system prompt string from the config.
    
        Returns:
            str: The system prompt string.
        """
        system_prompt = ("You are a phishing detection assistant. "
                        "Respond ONLY with valid JSON matching this schema:{ "
                        f'"classification": {self._config.get_allowed_classifications()}, '
                        f'"tactics_detected": {self._config.get_tactics_vocabulary()}, '
                        f'"threat_level": {list(self._config.get_threat_level_range())},'
                        f'"output_fields_rules": {self._config.get_output_fields()},'
                        f'"rule": {self._config.get_rules()},'
                        '}')
        
        return system_prompt

    def build_user_prompt(self, email_data: dict) -> str:
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
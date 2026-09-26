import json

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


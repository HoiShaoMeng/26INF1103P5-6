import json

def parse_response_content(content_str):
    """Parses the extracted content string into a Python dict.
    
    Args:
        content_str: The content string extracted from the API response.

    Returns:
        The dict, or None if it wasn't valid JSON.
    """
    try:
        return json.loads(content_str)
    except (json.JSONDecodeError, TypeError):
        print("Failed to parse content string as JSON: %s", content_str)
        return None

def receive_response(api_response_json):
    """Extracts the content string from the API response JSON.
    
    Args:
        api_response_json: The parsed JSON response from the API.

    Returns:
        The content body if present, otherwise None.
    """
    try:
        message = api_response_json["choices"][0]["message"]
        content_body = message["content"]
        return content_body

    except (KeyError, IndexError, TypeError):
        print("Unexpected API response structure: %s", api_response_json)
        return None


import os
import sys

from ai_client import ai_client
from openrouter import OpenRouter, errors

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "io"))
import io_manager


class OpenRouterClient(ai_client):
    def __init__(self, api_key, model, temperature, timeout_ms):
        self.__api_key = api_key
        self.__model = model
        self.__temperature = temperature
        self.__timeout_ms = timeout_ms


    def send_request(self, system_prompt:str, user_prompt:str) -> str | None:
        with OpenRouter(
                api_key=self.__api_key,
            ) as open_router:
                try:
                    response = open_router.chat.send(
                        model= self.__model,
                        messages=[
                            {"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}
                        ],
                        stream=False,
                        temperature=self.__temperature,
                        timeout_ms=self.__timeout_ms,  # 30 seconds
                    )
                    error = getattr(response, "error", None)
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
        return response


    def extract_content(self, response:str) -> str | None:
        try:
                response = response.model_dump()
                message = response["choices"][0]["message"]
                content_body = message["content"]
                return content_body
        
        except (KeyError, IndexError, TypeError, AttributeError):
            io_manager.display_error("API Response", f"Unexpected API response structure: {response}")
            return None


from ai_client import ai_client
from exceptions import AIConnectionError
from openrouter import OpenRouter, errors


class OpenRouterClient(ai_client):
    def __init__(self, api_key, model, temperature, timeout_ms):
        self.__api_key = api_key
        self.__model = model
        self.__temperature = temperature
        self.__timeout_ms = timeout_ms


    def send_request(self, system_prompt:str, user_prompt:str) -> str:
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
                    
        
                except errors.TooManyRequestsResponseError as e:
                    raise AIConnectionError(f"Rate limit hit (429): {e}")
                    
                except errors.UnauthorizedResponseError as e:
                    raise AIConnectionError(f"Invalid API Key (401) {e}")
                
                except errors.InternalServerResponseError as e:
                    raise AIConnectionError(f"Openrouter or upstream server error (500): {e}")

                except Exception as e: # OpenRouter is external and may fail in ways we did not anticipate
                    raise AIConnectionError("AI request failed: ",f"{e}") from e
        error = getattr(response, "error", None)
        if error:
            raise AIConnectionError(f"Openrouter returned an error: {error}")
        return self._extract_content(response)

    @staticmethod
    def _extract_content(response) -> str:
        try:
                response = response.model_dump()
                message = response["choices"][0]["message"]
                content_body = message["content"]
                return content_body
        
        except (KeyError, IndexError, TypeError, AttributeError):
            raise  AIConnectionError(f"Unexpected API response structure: {response}")

    @property
    def model(self):
        return self.__model
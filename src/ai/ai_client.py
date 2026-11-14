from abc import ABC, abstractmethod


class ai_client(ABC):
    @abstractmethod
    def send_request(self, system_prompt:str, user_prompt:str) -> str:
        return 

    @abstractmethod
    def extract_content(self, response:str) -> str:
        return 
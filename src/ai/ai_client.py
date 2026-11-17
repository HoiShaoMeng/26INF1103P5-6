from abc import ABC, abstractmethod


class AIClient(ABC):
    @abstractmethod
    def send_request(self, system_prompt:str, user_prompt:str) -> str:
        return 

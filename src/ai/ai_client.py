from abc import ABC, abstractmethod


class ai_client(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def send_request(self):
        return
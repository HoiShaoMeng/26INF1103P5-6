import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for layer in ("io", "ai", "logic", "data", "domain"):
    sys.path.insert(0, os.path.join(BASE_DIR, "src", layer))

from ai_manager import AIManager
from data_manager import DataManager

class TriageService:
    def __init__(self, ai: AIManager, data: DataManager, action_recommender, max_retries: int = 3, on_retry:callable = None):
        self.__ai = AIManager()
        self.__data = DataManager()
        self.__on_retry = on_retry
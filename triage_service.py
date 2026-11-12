import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for layer in ("io", "ai", "logic", "data", "domain"):
    sys.path.insert(0, os.path.join(BASE_DIR, "src", layer))

# src/ai
from ai_manager import AIManager

# src/data
from data_manager import DataManager
from report_history import ReportHistory

# src/logic
from logic_manager import ActionRecommender, CampaignDetector, SeverityClassifier

# src/domain
from blocklist import Blocklist
from screening_report import TriageDecision, ScreeningReport

class TriageService:
    def __init__(self, ai: AIManager, data: DataManager, action_recommender, max_retries: int = 3, on_retry:callable = None):
        self.__ai = ai
        self.__data = data
        self.__action_recommender = action_recommender
        self.__max_retries = max_retries
        self.__on_retry = on_retry

        self.__campaign_detector = CampaignDetector
        self.__history: ReportHistory | None = data.load_history() 
        self.__blocklist: Blocklist | None  = data.load_blocklist()

    def load_saved_data(self) -> None:
        return self.__history()

    def screen_email(self, email:dict) -> ScreeningOutcome:
        self.__ai.assess(email)
        return

    def _assess_with_retry(self, email:dict) -> dict:
        return

    def _decide(self, email:dict, ai_output:dict) -> TriageDecision:
        return

    def _save(self, email:dict, ai_output:dict, decision: TriageDecision) -> bool:
        return
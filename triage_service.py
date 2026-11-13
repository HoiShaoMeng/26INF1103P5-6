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
    def __init__(self, ai: AIManager, data: DataManager, action_recommender: ActionRecommender, max_retries: int = 3, on_retry:callable = None):
        self.__ai = ai
        self.__data = data
        self.__action_recommender = action_recommender
        self.__max_retries = max_retries
        self.__on_retry = on_retry

        self.__campaign_detector = CampaignDetector
        self.__history: ReportHistory | None = self.__data.load_history() 
        self.__blocklist: Blocklist | None  = data.load_blocklist()
        self.__severity_classifier = SeverityClassifier()

    def load_saved_data(self) -> None:
        self.__history = self.__data.load_history()

    def screen_email(self, email:dict) -> ScreeningReport:
        ai_outcome = self._assess_with_retry(email)
        decision = self._decide(email,ai_outcome)
        report = ScreeningReport.create(email, ai_outcome, decision)
        self._save(report)
        return report

    def _assess_with_retry(self, email:dict, retry_count = 0) -> dict:
        ai_outcome = self.__ai.assess(email)
        if ai_outcome["classification"] == "AI_UNAVAILABLE" & retry_count < self.__max_retries:
            self._assess_with_retry(email, retry_count+1)
        return ai_outcome

    def _decide(self, email:dict, ai_output:dict) -> TriageDecision:
        campaign_status = self.__campaign_detector.check_campaign(ai_output, self.__history.reports)
        severity_classification = self.__severity_classifier.classify(ai_output,campaign_status)
        recommended_action = self.__action_recommender.generate_recommended_action(severity_classification)
        decision = TriageDecision(severity_classification, campaign_status, recommended_action)
        return decision

    def _save(self, report:ScreeningReport) -> bool:
        self.__history.add(report)
        return self.__data.save_history(self.__history)
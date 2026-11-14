import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for layer in ("io", "ai", "logic", "data", "domain"):
    sys.path.insert(0, os.path.join(BASE_DIR, "src", layer))

from ai_manager import AIManager  # src/ai
from data_manager import DataManager  # src/data
from io_manager import IOManager
from logic_manager import (  # src/logic
    ActionRecommender,
    CampaignDetector,
    SeverityClassifier,
)
from report_history import ReportHistory  # src/data
from screening_report import ScreeningReport, TriageDecision  # src/domain


class TriageService: 
    def __init__(self, ai: AIManager, data: DataManager, io: IOManager, action_recommender: ActionRecommender, max_retries: int = 3):
        self.__ai = ai
        self.__data = data
        self.__io = io
        self.__action_recommender = action_recommender
        self.__max_retries = max_retries
        self.__campaign_detector = CampaignDetector()
        self.__history: ReportHistory | None = self.__data.load_history()
        # self.__blocklist: Blocklist | None  = data.load_blocklist()
        self.__severity_classifier = SeverityClassifier()
        self.__ai_result = None
        self.__recommended_action = None
        self.__severity_classification = None
        self.__campaign_status = None

    def load_saved_data(self) -> None:
        self.__history = self.__data.load_history()

    def screen_email(self, email:dict) -> ScreeningReport:
        ai_input = self.__io.get_ai_input(email)
        ai_outcome = self._assess_with_retry(ai_input)
        self.__ai_result = ai_outcome

        decision = self._decide(email,ai_outcome)
        report = ScreeningReport.create(email, ai_outcome, decision)
        self._save(report)
        return report

    def _assess_with_retry(self, email:dict, retry_count = 0) -> dict:
        ai_outcome = self.__ai.assess(email)
        if (ai_outcome["classification"] == "AI_UNAVAILABLE") & (retry_count < self.__max_retries):
            self._assess_with_retry(email, retry_count+1)
        self.ai_result = ai_outcome
        return ai_outcome

    def _decide(self, email:dict, ai_output:dict) -> TriageDecision:
        report_list = []
        for report in self.__history.reports:
            report_list.append(report.to_dict())
        campaign_status = self.__campaign_detector.check_campaign(email | ai_output, report_list)
        self.__campaign_status = campaign_status

        severity_classification = self.__severity_classifier.classify(ai_output,campaign_status)
        self.__severity_classification = severity_classification

        recommended_action = self.__action_recommender.generate_recommended_action(severity_classification)
        self.__recommended_action = recommended_action

        decision = TriageDecision(severity_classification, campaign_status, recommended_action)
        return decision

    def _save(self, report:ScreeningReport) -> bool:
        self.__history.add(report)
        return self.__data.save_history(self.__history)

    def get_ai_result(self)-> dict:
        return self.__ai_result

    def get_recommended_action(self)-> str:
            return self.__recommended_action

    def get_severity_classification(self)-> str:
            return self.__severity_classification

    def get_campaign_status(self)-> bool:
            return self.__campaign_status
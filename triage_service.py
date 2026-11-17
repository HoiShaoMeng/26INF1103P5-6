import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for layer in ("io", "ai", "logic", "data", "domain"):
    sys.path.insert(0, os.path.join(BASE_DIR, "src", layer))

from ai_manager import AI_UNAVAILABLE, AIManager  # src/ai
from data_manager import DataManager  # src/data
from exceptions import AIError  # src/ai
from io_manager import IOManager  # src/io
from logic_manager import (  # src/logic
    ActionRecommender,
    CampaignDetector,
    SeverityClassifier,
)
from screening_report import ScreeningReport, TriageDecision  # src/domain


#runs one screening from email to saved report: AI (with retries) -> campaign check -> severity -> action -> save.
#association: the AI, data, io and action recommender are created in main.py and passed in, this service only uses them.
class TriageService:
    def __init__(self, ai: AIManager, data: DataManager, io: IOManager, action_recommender: ActionRecommender,
                 max_retries: int = 3):
        self.__ai = ai
        self.__data = data
        self.__io = io
        self.__action_recommender = action_recommender
        self.__max_retries = max_retries
        self.__campaign_detector = CampaignDetector()
        self.__history = None
        self.__blocklist = None
        self.__ai_result = None
        self.__recommended_action = None
        self.__severity_classification = None
        self.__campaign_status = None
        self.__saved = False

    #loads the latest history and blocklist from disk before each screening, so a review made in option 3 is never
    #overwritten by an old copy. raises ReportStorageError if a file is corrupt, the app shows it and stops the screening.
    def load_saved_data(self) -> None:
        self.__history = self.__data.load_history()
        self.__blocklist = self.__data.load_blocklist()

    def screen_email(self, email: dict) -> ScreeningReport | None:
        if self.__history is None:
            self.load_saved_data()

        ai_outcome = self._assess_with_retry(self.__io.get_ai_input(email))
        self.__ai_result = ai_outcome

        decision = self._decide(email, ai_outcome)
        #a report without sender_email or reported_at cannot be used by the campaign check, so it is not saved
        try:
            report = ScreeningReport.create(email, ai_outcome, decision)
        except ValueError:
            self.__saved = False
            return None
        self.__saved = self._save(report)
        return report

    #asks the AI once, then retries up to max_retries times while the AI is unavailable.
    #any AI error (connection, bad JSON, wrong schema) becomes the AI_UNAVAILABLE result, so the app never crashes.
    def _assess_with_retry(self, ai_input: dict) -> dict:
        ai_outcome = self.__io.run_with_loading("Analysing email with AI", self._assess_once, ai_input)
        for attempt in range(1, self.__max_retries + 1):
            if ai_outcome.get("classification") != AI_UNAVAILABLE:
                break
            self.__io.display_error("AI", f"Retrying AI request ({attempt}/{self.__max_retries})...")
            ai_outcome = self.__io.run_with_loading("Analysing email with AI", self._assess_once, ai_input)
        return ai_outcome

    def _assess_once(self, ai_input: dict) -> dict:
        try:
            return self.__ai.assess(ai_input)
        except AIError as error:
            self.__io.display_error("AI", str(error))
            return AIManager.unavailable_result()

    def _decide(self, email: dict, ai_output: dict) -> TriageDecision:
        #campaign check runs before the new report is added, so the current email is never counted twice
        campaign_status = self.__campaign_detector.check_campaign(email, self.__history.to_dicts())
        self.__campaign_status = campaign_status

        #the blocklist and sender are passed so a sender already confirmed as phishing is always CRITICAL
        severity_classifier = SeverityClassifier(blocklist=self.__blocklist)
        severity_classification = severity_classifier.classify(ai_output, is_campaign=campaign_status,
                                                               sender_email=email["sender_email"])
        self.__severity_classification = severity_classification

        recommended_action = self.__action_recommender.generate_recommended_action(severity_classification)
        self.__recommended_action = recommended_action

        return TriageDecision(severity_classification, campaign_status, recommended_action)

    def _save(self, report: ScreeningReport) -> bool:
        self.__history.add(report)
        return self.__data.save_history(self.__history)

    def get_ai_result(self) -> dict:
        return self.__ai_result

    def get_recommended_action(self) -> str:
        return self.__recommended_action

    def get_severity_classification(self) -> str:
        return self.__severity_classification

    def get_campaign_status(self) -> bool:
        return self.__campaign_status

    #True if the last screened report was saved to reports.json
    def was_saved(self) -> bool:
        return self.__saved

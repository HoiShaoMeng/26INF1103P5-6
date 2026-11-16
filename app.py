import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for layer in ("io", "ai", "logic", "data", "domain"):
    sys.path.insert(0, os.path.join(BASE_DIR, "src", layer))

from ai_manager import AI_UNAVAILABLE
from dashboard import Dashboard
from data_manager import DataManager
from io_manager import IOManager
from json_list_file import ReportStorageError
from logic_manager import ActionRecommender
from review_prompt import ReviewPrompt
from review_service import ReviewService

from triage_service import TriageService


#runs the main menu and sends each choice to the right part of the app.
#association: every object it uses is created in main.py and passed in, the app does not own them.
class App:
    def __init__(self, triage: TriageService, data: DataManager, action_recommender: ActionRecommender, io: IOManager):
        self.__triage = triage
        self.__data = data
        self.__action_recommender = action_recommender
        self.__io = io

    def run(self) -> None:
        try:
            while True:
                answer = self.__io.prompt_menu_choice()
                if answer == "1":
                    self._screen_one_email()
                elif answer == "2":
                    self._view_reports_by_severity()
                elif answer == "3":
                    self._review_saved_report()
                elif answer == "4":
                    self._view_dashboard()
                elif answer == "5":
                    self.__io.display_exit_message()
                    return
        except (KeyboardInterrupt, EOFError):
            self.__io.display_exit_message()

    #menu option 1: screen one reported email from input to saved result
    def _screen_one_email(self) -> None:
        #load saved data before asking anything, so a corrupt file is shown first and nothing is typed for nothing
        try:
            self.__triage.load_saved_data()
        except ReportStorageError as error:
            self.__io.display_error("Data", str(error))
            return

        email_info = self.__io.prompt_email_fields()
        self.__triage.screen_email(email_info)

        ai_result = self.__triage.get_ai_result()
        if ai_result.get("classification") == AI_UNAVAILABLE:
            self.__io.display_error("AI", "the AI could not give a valid assessment",
                                    self.__triage.get_recommended_action())
        self.__io.display_screening_result(
            email_info,
            ai_result,
            self.__triage.get_severity_classification(),
            self.__triage.get_recommended_action(),
            self.__triage.get_campaign_status(),
        )
        if not self.__triage.was_saved():
            self.__io.display_error("Data", "the report could not be saved")

    #menu option 2: show the saved reports of one severity, most dangerous first
    def _view_reports_by_severity(self) -> None:
        severity_choice = self.__io.prompt_severity_choice()
        try:
            history = self.__data.load_history()
        except ReportStorageError as error:
            self.__io.display_error("Data", str(error))
            return
        matching = history.filter_by_severity(severity_choice).sort_by_threat_level()
        self.__io.display_report_list(matching.to_dicts(), severity_choice)

    #menu option 3 (new feature): an analyst confirms or rejects a saved report, the recovery step for phishing
    #the AI missed. confirmed phishing becomes CRITICAL, the sender is blocked, related archived reports are re-checked.
    def _review_saved_report(self) -> None:
        #load the history and blocklist first, a corrupt file stops here before anything changes
        try:
            history = self.__data.load_history()
            blocklist = self.__data.load_blocklist()
        except ReportStorageError as error:
            self.__io.display_error("Data", str(error))
            return

        #pick a severity and show that list, the same view as option 2
        severity_choice = self.__io.prompt_severity_choice()
        matching = history.filter_by_severity(severity_choice).sort_by_threat_level()
        self.__io.display_report_list(matching.to_dicts(), severity_choice)
        if len(matching) == 0:
            return

        #which report, which decision, who and why
        review_prompt = ReviewPrompt(self.__io.read_line, self.__io.show_error)
        report = matching.reports[review_prompt.ask_report_number(len(matching))]
        decision = review_prompt.ask_decision()
        if decision is None:
            return
        analyst = review_prompt.ask_text("Analyst name")
        reason = review_prompt.ask_text("Reason")

        #apply the decision, then send related archived reports back for a re-check if the sender was blocked
        review_service = ReviewService(self.__action_recommender, blocklist)
        review = review_service.apply_review(report, decision, analyst, reason)
        flagged = []
        if review.blocked_entry:
            flagged = review_service.flag_related(report, history)

        #the filtered list holds the same report objects as the full history, so saving the full history saves the review
        if not self.__data.save_history(history):
            self.__io.display_error("Data", "the review could not be saved")
            return
        if not self.__data.save_blocklist(blocklist):
            self.__io.display_error("Data", "the blocklist could not be saved")

        review_prompt.show_result(report.report_id, review, len(flagged))

    #menu option 4: the dashboard summary of every saved report
    def _view_dashboard(self) -> None:
        try:
            history = self.__data.load_history()
        except ReportStorageError as error:
            self.__io.display_error("Data", str(error))
            return
        model_type = self.__triage.get_ai_class().client.model
        dashboard = Dashboard.standard(model_type)
        self.__io.display_dashboard(dashboard.build(history.to_dicts()))

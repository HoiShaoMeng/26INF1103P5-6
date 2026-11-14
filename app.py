import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for layer in ("io", "ai", "logic", "data", "domain"):
    sys.path.insert(0, os.path.join(BASE_DIR, "src", layer))

from data_manager import DataManager
from io_manager import IOManager
from logic_manager import ActionRecommender

from triage_service import TriageService


class App:
    def __init__(self, triage: TriageService, data: DataManager, action_recommender: ActionRecommender, io: IOManager):
        self.__triage = triage
        self.__data = data
        self.__action_recommender = action_recommender
        self.__io = io
        # self.__actions : dict<str, Callable

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
                    self.__io.display_exit_message()
                    sys.exit()
        except (KeyboardInterrupt, EOFError):
            self.__io.display_exit_message()


    def _screen_one_email(self) -> None:
        email_info = self.__io.prompt_email_fields()
        self.__triage.screen_email(email_info)
        self.__io.display_screening_result(
            email_info, 
            self.__triage.get_ai_result(),
            self.__triage.get_severity_classification(), 
            self.__triage.get_recommended_action(), 
            self.__triage.get_campaign_status()
            )


    def _view_reports_by_severity(self) -> None:
        severity_choice = self.__io.prompt_severity_choice()
        report_history = self.__data.load_history()
        filtered = report_history.filter_by_severity(severity_choice)
        report_list = []
        for report in filtered.reports:
            report_list.append(report.to_dict())
        self.__io.display_report_list(report_list, severity_choice)


    def _review_saved_report(self) -> None:
        report_history = self.__data.load_history().sort_by_threat_level().reports
        report_list = []
        for report in report_history:
            report_list.append(report.to_dict())
        self.__io.display_report_list(report_list, "ALL")



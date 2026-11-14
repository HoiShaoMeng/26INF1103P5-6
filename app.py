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
        answer = self.__io.prompt_menu_choice()
        if answer == "1":
            self._screen_one_email()
        elif answer == "2":
            self.__view_reports_by_severity()
        elif answer == "3":
            self.__review_saved_reports()
        elif answer == "4":
            pass

        return

    def _screen_one_email(self) -> None:
        email_info = self.__io.prompt_email_fields()
        report = self.__triage.screen_email(email_info)
        return

    def _view_reports_by_severity(self) -> None:
        return

    def _review_saved_report(self) -> None:
        return


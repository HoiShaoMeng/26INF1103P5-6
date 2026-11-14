import os
import sys

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for layer in ("io", "ai", "logic", "data", "domain"):
    sys.path.insert(0, os.path.join(BASE_DIR, "src", layer))

from ai_manager import AIManager
from data_manager import DataManager
from io_manager import IOManager
from logic_manager import ActionRecommender
from open_router_client import OpenRouterClient
from prompt_config import PromptConfig

from app import App

# from json_report_repository import ReportStorageError
# from review_prompt import ReviewPrompt
# from review_service import ReviewService
# from screening_report import ScreeningReport, TriageDecision
from triage_service import TriageService

load_dotenv()
api_key=os.getenv("OPENROUTER_API_KEY")

prompt_config = PromptConfig.load_from_yaml_file()
client = OpenRouterClient(api_key, prompt_config.model, prompt_config.temperature, 30000)
action_recommender = ActionRecommender()
data = DataManager.for_project("")
ai = AIManager(prompt_config, client)
io = IOManager()
triage = TriageService(ai, data, io, action_recommender)
app = App(triage, data, action_recommender, io)


app.run()










# MAX_RETRIES = 3

# #menu option 1: screen one reported email from input to saved result
# def screen_one_email():
#     #(data, shao): load the saved history and the blocklist before asking anything, so a corrupt file is shown first
#     data = data_manager.DataManager.for_project(BASE_DIR)
#     try:
#         history = data.load_history()
#         blocklist = data.load_blocklist()
#     except ReportStorageError as error:
#         io_manager.display_error("Data", str(error))
#         return

#     report_dict = io_manager.prompt_email_fields()

#     config = ai_manager.load_prompt_config()
#     if config is None:
#         io_manager.display_error("AI", "prompt_config.yaml is missing or invalid",
#                              "Restore the file and run again.")
#         sys.exit(1)
#     system_prompt = ai_manager.build_system_prompt(config)
#     ai_input = io_manager.get_ai_input(report_dict)
#     user_prompt = ai_manager.build_user_prompt(ai_input)
    
#     # step 7 (ai, ping xuan)
#     response_dict = io_manager.run_with_loading("Analysing email with AI", ai_manager.ai_workflow, system_prompt, user_prompt, config)
#     for attempt in range(1, MAX_RETRIES + 1):  # retry up to 3 times if AI is unavailable
#         if response_dict["classification"] != ai_manager.AI_UNAVAILABLE:
#             break
#         io_manager.display_error("AI", f"Retrying AI request ({attempt}/{MAX_RETRIES})...")
#         response_dict = io_manager.run_with_loading("Analysing email with AI", ai_manager.ai_workflow, system_prompt, user_prompt, config)
    

#     #step 9 (logic, jeremy): campaign check, must run before the new report is added to history
#     campaign_detector = logic_manager.CampaignDetector()
#     is_campaign = campaign_detector.check_campaign(report_dict, history.to_dicts())

#     #step 10, 11 (logic, shao): decide the severity, pass the real campaign result and the sender for the blocklist
#     severity_classifier = logic_manager.SeverityClassifier(blocklist=blocklist)
#     severity = severity_classifier.classify(response_dict, is_campaign=is_campaign,
#                                             sender_email=report_dict["sender_email"])

#     #step 12 (logic, jeremy): turn the severity into the action text
#     action_recommender = logic_manager.ActionRecommender()
#     recommended_action = action_recommender.generate_recommended_action(severity)

#     #step 12 (data, shao): pack everything into one ScreeningReport, ValueError means it cannot be saved
#     decision = TriageDecision(severity, is_campaign, recommended_action)
#     saved = False
#     try:
#         new_report = ScreeningReport.create(report_dict, response_dict, decision)
#     except ValueError:
#         new_report = None

#     #step 13, 15 (data, shao): add the new report to the history and save it, True if saved, False if it failed
#     if new_report is not None:
#         history.add(new_report)
#         saved = data.save_history(history)

#     #step 16 (io, wei wen): show an AI error if the AI could not assess the email, then show the result
#     if response_dict.get("classification") == ai_manager.AI_UNAVAILABLE:
#         io_manager.display_error("AI", "the AI could not give a valid assessment", recommended_action)
    
#     #step 17 (io, wei wen): show the result to the user
#     io_manager.display_screening_result(report_dict, response_dict, severity, recommended_action, is_campaign)

#     #step 18 (io, wei wen): tell the user if the report could not be saved
#     if not saved:
#         io_manager.display_error("Data", "the report could not be saved")

# #menu option 2: show the saved reports of one severity, e.g. all CRITICAL ones to act on first
# def view_reports_by_severity():
#     #io: ask which severity to view
#     severity = io_manager.prompt_severity_choice()

#     #(data, shao): load the saved reports into one ReportHistory object
#     try:
#         history = data_manager.DataManager.for_project(BASE_DIR).load_history()
#     except ReportStorageError as error:
#         io_manager.display_error("Data", str(error))
#         return

#     #(data, shao): keep only the matching reports, then put the most dangerous first
#     matching_reports = history.filter_by_severity(severity).sort_by_threat_level()

#     #io: show the matching reports, or a message if there are none
#     io_manager.display_report_list(matching_reports.to_dicts(), severity)

# #menu option 3 (new feature, shao): an analyst confirms or rejects a saved report, the recovery step for
# #phishing the AI missed. confirmed phishing becomes CRITICAL, the sender is blocked, related archived reports are re-checked.
# def review_saved_report():
#     #(data): load the history and blocklist, a corrupt file stops here before anything changes
#     data = data_manager.DataManager.for_project(BASE_DIR)
#     try:
#         history = data.load_history()
#         blocklist = data.load_blocklist()
#     except ReportStorageError as error:
#         io_manager.display_error("Data", str(error))
#         return

#     #io: pick a severity and show that list, the same view as option 2
#     severity = io_manager.prompt_severity_choice()
#     matching_reports = history.filter_by_severity(severity).sort_by_threat_level()
#     io_manager.display_report_list(matching_reports.to_dicts(), severity)
#     if len(matching_reports) == 0:
#         return

#     #io: which report, which decision, who and why
#     review_prompt = ReviewPrompt(io_manager.read_line, io_manager.show_error)
#     report = matching_reports.reports[review_prompt.ask_report_number(len(matching_reports))]
#     decision = review_prompt.ask_decision()
#     if decision is None:
#         return
#     analyst = review_prompt.ask_text("Analyst name")
#     reason = review_prompt.ask_text("Reason")

#     #logic: apply the decision, then send related archived reports back for a re-check if it was phishing
#     review_service = ReviewService(logic_manager.ActionRecommender(), blocklist)
#     review = review_service.apply_review(report, decision, analyst, reason)
#     flagged = []
#     if review.blocked_entry:
#         flagged = review_service.flag_related(report, history)

#     #data: the filtered list holds the same report objects as the full history, so saving
#     #the full history saves the review too
#     if not data.save_history(history):
#         io_manager.display_error("Data", "the review could not be saved")
#         return
#     if not data.save_blocklist(blocklist):
#         io_manager.display_error("Data", "the blocklist could not be saved")

#     #io: show what changed
#     review_prompt.show_result(report.report_id, review, len(flagged))

# #shows the menu until the user chooses exit
# def main():
#     while True:
#         choice = io_manager.prompt_menu_choice()
#         if choice == "1":
#             screen_one_email()
#         elif choice == "2":
#             view_reports_by_severity()
#         elif choice == "3":
#             review_saved_report()
#         else:
#             break

# if __name__ == "__main__":
#     main()


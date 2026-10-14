import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for layer in ("io", "ai", "logic", "data"):
    sys.path.insert(0, os.path.join(BASE_DIR, "src", layer))

import ai_manager
import data_manager
import io_manager
import logic_manager

MAX_RETRIES = 3

#menu option 1: screen one reported email from input to saved result
def screen_one_email():
    report_dict = io_manager.prompt_email_fields()

    config = ai_manager.load_prompt_config()
    if config is None:
        io_manager.display_error("AI", "prompt_config.yaml is missing or invalid",
                             "Restore the file and run again.")
        sys.exit(1)
    system_prompt = ai_manager.build_system_prompt(config)
    ai_input = io_manager.get_ai_input(report_dict)
    user_prompt = ai_manager.build_user_prompt(ai_input)
    
    # step 7 (ai, ping xuan)
    response_dict = io_manager.run_with_loading("Analysing email with AI", ai_manager.ai_workflow, system_prompt, user_prompt, config)
    for attempt in range(1, MAX_RETRIES + 1):  # retry up to 3 times if AI is unavailable
        if response_dict["classification"] != ai_manager.AI_UNAVAILABLE:
            break
        io_manager.display_error("AI", f"Retrying AI request ({attempt}/{MAX_RETRIES})...")
        response_dict = io_manager.run_with_loading("Analysing email with AI", ai_manager.ai_workflow, system_prompt, user_prompt, config)
    
    #step 8 (data, jeremy): load the saved report history
    history = data_manager.read_file()

    #step 9 (logic, jeremy): campaign check, must run before the new report is added to history
    is_campaign = logic_manager.check_campaign(report_dict, history)

    #step 10, 11 (logic, shao): decide the severity, pass the real campaign result, never a hard-coded False
    severity = logic_manager.classify_severity(response_dict, is_campaign=is_campaign)

    #step 12 (logic, jeremy): turn the severity into the action text
    recommended_action = logic_manager.generate_recommended_action(severity)

    #step 12 (data, shao): pack everything into one report, {} means it cannot be saved
    new_report = data_manager.format_report(report_dict, response_dict, is_campaign, severity, recommended_action)

    #step 13 (main): add the new report to the history, skipped if it is {}
    saved = False
    if new_report:
        history.append(new_report)

        #step 15 (data, shao): save the whole history, True if saved, False if it failed
        saved = data_manager.write_file(history)

    #step 16 (io, wei wen): show an AI error if the AI could not assess the email, then show the result
    if response_dict.get("classification") == ai_manager.AI_UNAVAILABLE:
        io_manager.display_error("AI", "the AI could not give a valid assessment", recommended_action)
    
    #step 17 (io, wei wen): show the result to the user
    io_manager.display_screening_result(report_dict, response_dict, severity, recommended_action, is_campaign)

    #step 18 (io, wei wen): tell the user if the report could not be saved
    if not saved:
        io_manager.display_error("Data", "the report could not be saved")

#menu option 2: show the saved reports of one severity, e.g. all CRITICAL ones to act on first
def view_reports_by_severity():
    #io: ask which severity to view
    severity = io_manager.prompt_severity_choice()

    #(data, shao): load the saved history and keep only the matching reports
    history = data_manager.read_file()
    matching_reports = data_manager.filter_by_severity(history, severity)

    #(data, shao): put the most dangerous reports first
    matching_reports = data_manager.sort_by_threat_level(matching_reports)

    #io: show the matching reports, or a message if there are none
    io_manager.display_report_list(matching_reports, severity)


#shows the menu until the user chooses exit
def main():
    while True:
        choice = io_manager.prompt_menu_choice()
        if choice == "1":
            screen_one_email()
        elif choice == "2":
            view_reports_by_severity()
        else:
            break

if __name__ == "__main__":
    main()

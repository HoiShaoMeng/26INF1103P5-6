import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for layer in ("io", "ai", "logic", "data"):
    sys.path.insert(0, os.path.join(BASE_DIR, "src", layer))

import io_manager
import ai_manager
import logic_manager
import data_manager

if __name__ == "__main__":
    report_dict = io_manager.prompt_email_fields()
    
    system_prompt = ai_manager.build_system_prompt(ai_manager.load_prompt_config())
    ai_input = io_manager.get_ai_input(report_dict)
    user_prompt = ai_manager.build_user_prompt(ai_input)
    response_dict = dict()
    status = False
    while not response_dict:
        response_dict = ai_manager.ai_workflow(system_prompt, user_prompt, response_dict)

    #step 10 (data, jeremy): load the saved report history
    history = data_manager.read_file()

    #step 11 (logic, jeremy): campaign check, must run before the new report is added to history
    is_campaign = logic_manager.check_campaign(report_dict, history)

    #step 12 (logic, shao): decide the severity, pass the real campaign result, never a hard-coded False
    severity = logic_manager.classify_severity(response_dict, is_campaign=is_campaign)

    #step 13 (logic, jeremy): turn the severity into the action text
    recommended_action = logic_manager.generate_recommended_action(severity)

    #step 14 (data, shao): pack everything into one report, {} means it cannot be saved
    new_report = data_manager.format_report(report_dict, response_dict, is_campaign, severity, recommended_action)

    #step 15 (main): add the new report to the history, skipped if it is {}
    saved = False
    if new_report:
        history.append(new_report)

        #step 16 (data, shao): save the whole history, True if saved, False if it failed
        saved = data_manager.write_file(history)

    print(response_dict)

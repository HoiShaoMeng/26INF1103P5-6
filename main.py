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
    user_prompt = ai_manager.build_user_prompt(report_dict)
    response_dict = dict()
    status = False
    while not response_dict:
        response_dict = ai_manager.ai_workflow(system_prompt, user_prompt, response_dict)

    print(response_dict)
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
    system_prompt = ai_manager.build_system_prompt(ai_manager.load_prompt_config())
    user_prompt = ai_manager.build_user_prompt()
    res =ai_manager.send_request(system_prompt, user_prompt)
    print(ai_manager.receive_response(res))
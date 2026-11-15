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
from triage_service import TriageService

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

#builds every object once and passes them in, so each class only uses what it is given
prompt_config = PromptConfig.load_from_yaml_file()
client = OpenRouterClient(api_key, prompt_config.model, prompt_config.temperature, 30000)
action_recommender = ActionRecommender()
#data/ is found from this file's folder, so the app works from any working directory (and in Docker)
data = DataManager.for_project(BASE_DIR)
ai = AIManager(prompt_config, client)
io = IOManager()
triage = TriageService(ai, data, io, action_recommender)
app = App(triage, data, action_recommender, io)

if __name__ == "__main__":
    app.run()

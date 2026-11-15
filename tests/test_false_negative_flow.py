"""End-to-end test of the professor's question: a malicious email ends up LOG_ONLY, then what?

Runs the real App and TriageService with a fake AI and a temp data folder, so no live API or real data is used.
"""

import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
for layer in ("io", "ai", "logic", "data", "domain"):
    sys.path.insert(0, os.path.join(ROOT, "src", layer))
sys.path.insert(0, ROOT)

from data_manager import DataManager  # type: ignore
from io_manager import IOManager  # type: ignore
from logic_manager import ActionRecommender  # type: ignore

from app import App  # type: ignore
from triage_service import TriageService  # type: ignore

# the AI is fooled: a phishing email looks harmless, so it is scored low
FOOLED_AI_REPLY = {
    "classification": "benign",
    "threat_level": 10,
    "tactics_detected": [],
    "suspicious_urls": [],
    "suspicious_attachments": [],
    "sender_domain_mismatch": False,
}


# stand-in for the AI manager: always gives the fooled reply, never calls the internet
class FooledAI:
    def assess(self, email):
        return dict(FOOLED_AI_REPLY)


# one email typed into menu option 1 (menu: 1 screen, 2 view, 3 review, 4 dashboard, 5 exit)
def screen(sender, subject):
    return ["1", sender, "", subject, "click here", "END", "n", "n"]


def run_app(tmp_path, answers):
    typed = iter(answers + ["5"])
    printed = []
    io = IOManager(read_input=lambda prompt="": next(typed), print_line=printed.append)
    data = DataManager.for_project(tmp_path)
    recommender = ActionRecommender()
    App(TriageService(FooledAI(), data, io, recommender), data, recommender, io).run()
    return data, "\n".join(printed)


def severities(data):
    return {report.to_dict()["subject"]: report.severity for report in data.load_history().reports}


def test_missed_phishing_is_saved_as_log_only_not_lost(tmp_path):
    data, _ = run_app(tmp_path, screen("it-desk@evil.com", "Password reset"))
    assert severities(data) == {"Password reset": "LOG_ONLY"}


def test_analyst_review_recovers_a_missed_phishing_email(tmp_path, capsys):
    #two phishing emails from evil.com are missed and saved as LOG_ONLY
    answers = screen("it-desk@evil.com", "Password reset") + screen("hr@evil.com", "Payslip")
    #option 3: view LOG_ONLY (3), pick report 1, confirmed phishing (1), analyst name, reason
    answers += ["3", "3", "1", "1", "Shao", "fake login page"]
    #a third email from the same attacker arrives after the review
    answers += screen("ceo@evil.com", "Urgent wire transfer")

    data, output = run_app(tmp_path, answers)
    result = severities(data)

    #the reviewed email is upgraded and the related one is sent back for a human check
    assert result["Password reset"] == "CRITICAL"
    assert result["Payslip"] == "NEEDS_REVIEW"
    #the next email from the blocked domain is CRITICAL straight away, even though the AI was fooled again
    assert result["Urgent wire transfer"] == "CRITICAL"
    assert data.load_blocklist().contains_sender("anyone@evil.com")

    #the audit record keeps who decided, why, and the original AI result
    reviewed = next(r for r in data.load_history().reports if r.to_dict()["subject"] == "Password reset")
    assert reviewed.review.analyst == "Shao"
    assert reviewed.review.previous_severity == "LOG_ONLY"
    assert reviewed.to_dict()["classification"] == "benign"
    #the review screen (printed by ReviewPrompt) shows what changed
    shown = output + capsys.readouterr().out
    assert "REVIEW SAVED" in shown
    assert "LOG_ONLY -> CRITICAL" in shown


def test_safety_net_stops_flagged_link_being_log_only(tmp_path):
    #the AI scores it low but still flags the link, so it must go to a person, not the archive
    class LowScoreButFlaggedLink(FooledAI):
        def assess(self, email):
            return dict(FOOLED_AI_REPLY, suspicious_urls=["http://bit.ly/x"])

    typed = iter(screen("a@shop.com", "Your parcel") + ["5"])
    io = IOManager(read_input=lambda prompt="": next(typed), print_line=lambda line: None)
    data = DataManager.for_project(tmp_path)
    recommender = ActionRecommender()
    App(TriageService(LowScoreButFlaggedLink(), data, io, recommender), data, recommender, io).run()

    assert severities(data) == {"Your parcel": "NEEDS_REVIEW"}

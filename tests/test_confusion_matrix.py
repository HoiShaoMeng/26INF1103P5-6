


import io
import json
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
for layer in ("io", "ai", "logic", "data", "domain"):
    sys.path.insert(0, os.path.join(ROOT, "src", layer))
sys.path.insert(0, ROOT)

from ai_manager import AIManager
from analyst_review import ReviewDecision
from data_manager import DataManager
from exceptions import AIConnectionError
from io_manager import IOManager
from logic_manager import ActionRecommender
from mock_ai_client import MockAIClient
from prompt_config import PromptConfig
from review_service import ReviewService

from triage_service import TriageService

FLAGGED = {"CRITICAL", "NEEDS_REVIEW"}

def ai_reply(classfication, threat_level, tactics=(), urls=(), attachments=(), mismatch=False) -> str:
    return json.dumps({
        "classification": classfication,
        "threat_level": threat_level,
        "tactics_detected": list(tactics),
        "suspicious_urls": list(urls),
        "suspicious_attachments": list(attachments),
        "sender_domain_mismatch": mismatch,
    })

def email(sender, subject, reported_at="2026-11-17T09:00:00+00:00", urls=(), attachments=()):
    return {
        "sender_email": sender,
        "sender_name": "",
        "subject": subject,
        "body": "test body",
        "urls": list(urls),
        "attachments": [{"filename": name} for name in attachments],
        "reported_at": reported_at,
    }

class Pipeline:
    """The real TriageService, AiManager and DataManager wired together, with the AI replied scripted."""

    def __init__(self, tmp_path, replies):
        self.data = DataManager.for_project(tmp_path)
        self.recommender = ActionRecommender()
        self.service = TriageService(
            AIManager(PromptConfig.load_from_yaml_file(), MockAIClient(replies)),
            self.data, IOManager(output=io.StringIO()), self.recommender,
        )

    def screen(self, email_record) -> str:
        self.service.load_saved_data() # same as the app: latest history and blocklist before each screening
        self.service.screen_email(email_record)
        return self.service.get_severity_classification()

    def review_last(self, decision):
        history = self.data.load_history()
        blocklist = self.data.load_blocklist()
        report = history.reports[-1]
        review_service = ReviewService(self.recommender, blocklist)
        review = review_service.apply_review(report, decision, "analyst", "checked by hand")
        flagged = review_service.flag_related(report, history) if review.blocked_entry else []
        self.data.save_history(history)
        self.data.save_blocklist(blocklist)
        return report, review, flagged

    def saved_severities(self) -> list:
        return [report.severity for report in self.data.load_history().reports]


# -------------------------------------------------------------------- TRUE POSITIVES
# phishing email, and the system flags it

@pytest.mark.parametrize("record, reply, expected", [
    # CEO wire-transfer scam: high threat level -> CRITICAL
    (email("john.tan@yourcompany-support.com", "Urgent wire transfer"),
     ai_reply("spear-phishing", 90, ["impersonation", "financial_request"], mismatch=True), "CRITICAL"),
    # rule A: domain mismatch + a suspicious link is CRITICAL even with a middling threat level
    (email("it@micros0ft-help.com", "Verify your mailbox", urls=["http://micros0ft-help.com/login"]),
     ai_reply("phishing", 60, urls=["http://micros0ft-help.com/login"], mismatch=True), "CRITICAL"),
    # rule B: a suspicious band (50-79) with 2+ tactics is escalated to CRITICAL
    (email("hr@payroll-update.co", "Confirm your bank details"),
     ai_reply("phishing", 65, ["credential_harvesting", "urgency_pressure"]), "CRITICAL"),
    # a suspicious band with one tactic stays NEEDS_REVIEW, still flagged
    (email("delivery@parcel-track.info", "Missed delivery"),
     ai_reply("phishing", 55, ["urgency_pressure"]), "NEEDS_REVIEW"),
    # fake invoice with a suspicious attachment and a domain mismatch -> CRITICAL
    (email("billing@acc0unts-payable.net", "Invoice overdue", attachments=["invoice.pdf.exe"]),
     ai_reply("phishing", 70, attachments=["invoice.pdf.exe"], mismatch=True), "CRITICAL"),
])
def test_true_positive_phishing_is_flagged(tmp_path, record, reply, expected):
    severity = Pipeline(tmp_path, [reply]).screen(record)
    assert severity in FLAGGED
    assert severity == expected


def test_true_positive_campaign_third_report_is_critical(tmp_path):
    replies = [ai_reply("spam", 30)] * 3
    pipeline = Pipeline(tmp_path, replies)
    pipeline.screen(email("a@promo-blast.biz", "Offer 1", "2026-11-17T08:00:00+00:00"))
    pipeline.screen(email("b@promo-blast.biz", "Offer 2", "2026-11-17T09:00:00+00:00"))
    assert pipeline.screen(email("c@promo-blast.biz", "Offer 3", "2026-11-17T10:00:00+00:00")) == "CRITICAL"


# -------------------------------------------------------------------- TRUE NEGATIVES
# safe email, and the system archives it

@pytest.mark.parametrize("record, reply", [
    # company newsletter
    (email("news@yourcompany.com", "November newsletter"), ai_reply("benign", 5)),
    # ordinary marketing spam, nothing dangerous
    (email("deals@shop.example", "Black Friday sale"), ai_reply("spam", 30)),
    # a real link that the AI did not flag as suspicious
    (email("noreply@github.com", "New sign-in", urls=["https://github.com/settings"]), ai_reply("benign", 10)),
    # threat level just under the review band
    (email("events@yourcompany.com", "Team lunch"), ai_reply("benign", 49)),
])
def test_true_negative_safe_email_is_archived(tmp_path, record, reply):
    pipeline = Pipeline(tmp_path, [reply])
    assert pipeline.screen(record) == "LOG_ONLY"
    assert pipeline.service.get_recommended_action() == "Archive the report. No further action required."

# -------------------------------------------------------------------- FALSE POSITIVES
# safe email, but the AI thinks it is phishing, so the system flags it

def test_false_positive_safe_email_is_flagged_by_the_ai(tmp_path):
    # a real password-expiry notice from internal IT, which the AI scores as phishing
    pipeline = Pipeline(tmp_path, [ai_reply("phishing", 85, ["urgency_pressure"])])
    assert pipeline.screen(email("it@yourcompany.com", "Password expires in 3 days")) == "CRITICAL"

def test_false_positive_is_corrected_by_analyst_confirming_safe(tmp_path):
    pipeline = Pipeline(tmp_path, [ai_reply("phishing", 85, ["urgency_pressure"])])
    assert pipeline.screen(email("it@yourcompany.com", "Password expires in 3 days")) == "CRITICAL"

    report, review, flagged = pipeline.review_last(ReviewDecision.CONFIRMED_SAFE)

    assert pipeline.saved_severities() == ["LOG_ONLY"]
    assert review.previous_severity == "CRITICAL" # audit trail keeps what the system first said
    assert review.blocked_entry == ""               # a safe sender is never blocked
    assert flagged == []
    assert report.ai_output["classification"] == "phishing" # the original AI result is not edited


def test_false_positive_confirmed_safe_does_not_block_the_sender(tmp_path):
    replies = [ai_reply("phishing", 85), ai_reply("benign", 5)]
    pipeline = Pipeline(tmp_path, replies)
    pipeline.screen(email("it@yourcompany.com", "Password expires", "2026-11-17T09:00:00+00:00"))
    pipeline.review_last(ReviewDecision.CONFIRMED_SAFE)
    # the next normal email from the sneder is archived, not CRITICAL
    assert pipeline.screen(email("it@yourcompany.com", "Office closed Friday", "2026-11-18T09:00:00+00:00")) == "LOG_ONLY"

# -------------------------------------------------------------------- FALSE NEGATIVES
# phishing email, but the AI is fooled, so the system archives it

def test_false_negative_fooled_ai_archives_the_phishing(tmp_path):
    pipeline = Pipeline(tmp_path, [ai_reply("benign", 10)])
    assert pipeline.screen(email("ceo@yourcompany-mail.org", "Quick question")) == "LOG_ONLY"


def test_false_negative_is_caught_by_the_suspicious_evidence_safety_net(tmp_path):
    record = email("it@helpdesk-reset.com", "Reset", urls=["http://helpdesk-reset.com/a"])
    reply = ai_reply("benign", 15, urls=["http://helpdesk-reset.com/a"])
    assert Pipeline(tmp_path, [reply]).screen(record) == "NEEDS_REVIEW"


def test_false_negative_is_avoided_when_the_ai_is_down(tmp_path):
    pipeline = Pipeline(tmp_path, [AIConnectionError("down")] * 4)
    assert pipeline.screen(email("ceo@yourcompany-mail.org", "Quick question")) == "NEEDS_REVIEW"


def test_false_negative_recovery_confirm_block_and_recheck(tmp_path):
    replies = [ai_reply("benign", 10)] * 3
    pipeline = Pipeline(tmp_path, replies)

    # two reports from the attacker are archived (missed)
    pipeline.screen(email("ceo@yourcompany-mail.org", "Quick question", "2026-11-17T09:00:00+00:00"))
    pipeline.screen(email("cfo@yourcompany-mail.org", "Are you free?", "2026-11-17T10:00:00+00:00"))
    assert pipeline.saved_severities() == ["LOG_ONLY", "LOG_ONLY"]

    # an analyst confirmes the second one is phishing
    report, review, flagged = pipeline.review_last(ReviewDecision.CONFIRMED_PHISHING)
    assert review.blocked_entry == "yourcompany-mail.org"
    assert [r.report_id for r in flagged] != [report.report_id]
    assert pipeline.saved_severities() == ["NEEDS_REVIEW", "CRITICAL"] # the first is sent back for a re-check

    # the attacker's next email is CRITICAL straight away, even though the AI is still fooled
    later = email("ceo@yourcompany-mail.org", "Gift cards", "2026-11-19T09:00:00+00:00")
    assert pipeline.screen(later) == "CRITICAL"



# -------------------------------------------------------------------- SUMMARY
# a small labelled set run through the pipeline, counted into a confusion matrix

LABELLED_SET = [
    # (is_really_phishing, email, scripted AI reply)
    (True, email("john.tan@yourcompany-support.com", "Wire transfer", "2026-11-10T09:00:00+00:00"),
     ai_reply("spear-phishing", 90, ["impersonation", "financial_request"], mismatch=True)),           # TP
    (True, email("it@micros0ft-help.com", "Verify", "2026-11-11T09:00:00+00:00", urls=["http://m.co/x"]),
     ai_reply("phishing", 60, urls=["http://m.co/x"], mismatch=True)),                                 # TP
    (True, email("ceo@yourcompany-mail.org", "Quick question", "2026-11-12T09:00:00+00:00"),
     ai_reply("benign", 10)),                                                                          # FN
    (False, email("news@yourcompany.com", "Newsletter", "2026-11-13T09:00:00+00:00"),
     ai_reply("benign", 5)),                                                                           # TN
    (False, email("deals@shop.example", "Sale", "2026-11-14T09:00:00+00:00"),
     ai_reply("spam", 30)),                                                                            # TN
    (False, email("it@yourcompany.com", "Password expires", "2026-11-15T09:00:00+00:00"),
     ai_reply("phishing", 85, ["urgency_pressure"])),                                                  # FP
]

def test_confusion_matrix_on_the_labelled_set(tmp_path):
    pipeline = Pipeline(tmp_path, [reply for _, _, reply in LABELLED_SET])
    counts = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}

    for is_phishing, record, _ in LABELLED_SET:
        flagged = pipeline.screen(record) in FLAGGED
        if is_phishing:
            counts["TP" if flagged else "FN"] += 1
        else:
            counts ["FP" if flagged else "TN"] += 1

    assert counts == {"TP": 2, "FP": 1, "TN": 2, "FN": 1}
    assert len(pipeline.saved_severities()) == len(LABELLED_SET) # every report is saved, missed ones included
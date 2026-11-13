"""screening_report: one reported email together with the AI result and the triage decision about it."""

import uuid

from analyst_review import AnalystReview
from attachment import Attachment


#what the business rules decided for one report. it cannot change after it is created,
#a new decision replaces the old one (e.g. after an analyst review) instead of editing it.
class TriageDecision:

    def __init__(self, severity: str, is_campaign: bool, recommended_action: str):
        #str() so a Severity member is saved as plain text, e.g. "CRITICAL"
        self._severity = str(severity)
        self._is_campaign = bool(is_campaign)
        self._recommended_action = recommended_action

    @property
    def severity(self) -> str:
        return self._severity

    @property
    def is_campaign(self) -> bool:
        return self._is_campaign

    @property
    def recommended_action(self) -> str:
        return self._recommended_action


#one screened email: the email fields from io, the AI output, the decision from logic, and an optional analyst review.
#keeping them in one object gives each report an id, and changes only happen through apply_review()
#and flag_for_recheck(), so the original AI result and the audit trail cannot be edited by accident.
class ScreeningReport:

    #the email fields copied from the io record, in the order they are saved
    EMAIL_FIELDS = ("sender_email", "sender_name", "subject", "body", "urls", "reported_at")
    #the AI fields copied from the AI output, in the order they are saved
    AI_FIELDS = ("classification", "threat_level", "tactics_detected", "suspicious_urls",
                 "suspicious_attachments", "sender_domain_mismatch")

    def __init__(self, email: dict, ai_output: dict, decision: TriageDecision,
                 report_id: str | None = None, review: AnalystReview | None = None, flagged_by: str = ""):
        #a short unique id so one saved report can be pointed to, e.g. by a review
        self._report_id = report_id or uuid.uuid4().hex[:8]
        self._email = {field: email.get(field) for field in self.EMAIL_FIELDS}
        self._email["urls"] = self._email["urls"] or []
        self._email["sender_name"] = self._email["sender_name"] or ""
        #each saved attachment becomes an Attachment, so its extension is always worked out the same way
        self._attachments = [Attachment.from_dict(item) for item in email.get("attachments") or []
                             if isinstance(item, dict) and isinstance(item.get("filename"), str)]
        #the original AI result is kept as it was, even after a review changes the severity
        self._ai_output = {field: ai_output.get(field) for field in self.AI_FIELDS}
        for field in ("tactics_detected", "suspicious_urls", "suspicious_attachments"):
            self._ai_output[field] = self._ai_output[field] or []
        self._decision = decision
        self._review = review
        #the id of the confirmed phishing report that sent this one back for a re-check, "" if none
        self._flagged_by = flagged_by

    #builds a new report from a screening, raises ValueError if campaign detection could not use it later
    @classmethod
    def create(cls, record: dict, ai_output: dict, decision: TriageDecision) -> "ScreeningReport":
        if not isinstance(record, dict) or not record.get("sender_email") or not record.get("reported_at"):
            raise ValueError("A report needs sender_email and reported_at.")
        if not isinstance(ai_output, dict):
            ai_output = {}
        return cls(record, ai_output, decision)

    #rebuilds a saved report. old Part 1 reports have no report_id, so they get a new one here.
    #missing fields get safe defaults instead of crashing, so an old or partly broken report is never lost.
    @classmethod
    def from_dict(cls, data: dict) -> "ScreeningReport":
        decision = TriageDecision(data.get("severity") or "", data.get("is_campaign"),
                                  data.get("recommended_action") or "")
        review = None
        if isinstance(data.get("review"), dict):
            try:
                review = AnalystReview.from_dict(data["review"])
            except ValueError:
                review = None
        return cls(data, data, decision, data.get("report_id"), review, data.get("flagged_by") or "")

    # --- read-only access ---
    @property
    def report_id(self) -> str:
        return self._report_id

    @property
    def sender_email(self) -> str:
        return self._email["sender_email"] or ""

    @property
    def reported_at(self) -> str:
        return self._email["reported_at"] or ""

    @property
    def attachments(self) -> list:
        return list(self._attachments)

    #a copy, so outside code cannot change the saved AI result
    @property
    def ai_output(self) -> dict:
        return dict(self._ai_output)

    @property
    def threat_level(self):
        return self._ai_output["threat_level"]

    @property
    def decision(self) -> TriageDecision:
        return self._decision

    @property
    def severity(self) -> str:
        return self._decision.severity

    @property
    def review(self) -> AnalystReview | None:
        return self._review

    @property
    def flagged_by(self) -> str:
        return self._flagged_by

    # --- changes, only through these methods ---
    #an analyst confirmed or rejected this report: keep the review and use the new decision
    def apply_review(self, review: AnalystReview, new_decision: TriageDecision) -> None:
        self._review = review
        self._decision = new_decision

    #a related report was confirmed as phishing, so send this one back for a manual re-check
    def flag_for_recheck(self, new_decision: TriageDecision, flagged_by: str) -> None:
        self._decision = new_decision
        self._flagged_by = flagged_by

    #the one flat record saved in reports.json: id, 7 io fields, 6 AI fields, 3 logic fields, then review info
    def to_dict(self) -> dict:
        return {
            "report_id": self._report_id,
            "sender_email": self._email["sender_email"],
            "sender_name": self._email["sender_name"],
            "subject": self._email["subject"],
            "body": self._email["body"],
            "urls": list(self._email["urls"]),
            "attachments": [attachment.to_dict() for attachment in self._attachments],
            "reported_at": self._email["reported_at"],
            **self.ai_output,
            "is_campaign": self._decision.is_campaign,
            "severity": self._decision.severity,
            "recommended_action": self._decision.recommended_action,
            "review": self._review.to_dict() if self._review else None,
            "flagged_by": self._flagged_by,
        }

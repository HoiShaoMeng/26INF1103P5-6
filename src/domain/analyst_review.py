"""analyst_review: a person's final decision on a screened report, kept as an audit record."""

from enum import StrEnum


#the two decisions an analyst can make after checking a report themselves
class ReviewDecision(StrEnum):
    CONFIRMED_PHISHING = "CONFIRMED_PHISHING"
    CONFIRMED_SAFE = "CONFIRMED_SAFE"


#one review of one report: who decided what, why, when, and how the severity changed.
#nothing can be changed after it is created, so the audit trail cannot be edited later.
class AnalystReview:

    def __init__(self, decision: ReviewDecision, analyst: str, reason: str, reviewed_at: str,
                 previous_severity: str, new_severity: str, blocked_entry: str = ""):
        self._decision = ReviewDecision(decision)
        self._analyst = analyst
        self._reason = reason
        self._reviewed_at = reviewed_at
        self._previous_severity = str(previous_severity)
        self._new_severity = str(new_severity)
        self._blocked_entry = blocked_entry

    @property
    def decision(self) -> ReviewDecision:
        return self._decision

    @property
    def analyst(self) -> str:
        return self._analyst

    @property
    def reason(self) -> str:
        return self._reason

    @property
    def reviewed_at(self) -> str:
        return self._reviewed_at

    @property
    def previous_severity(self) -> str:
        return self._previous_severity

    @property
    def new_severity(self) -> str:
        return self._new_severity

    #the blocklist entry this review added, "" if nothing was blocked
    @property
    def blocked_entry(self) -> str:
        return self._blocked_entry

    #saved form used inside the report in reports.json
    def to_dict(self) -> dict:
        return {
            "decision": str(self._decision),
            "analyst": self._analyst,
            "reason": self._reason,
            "reviewed_at": self._reviewed_at,
            "previous_severity": self._previous_severity,
            "new_severity": self._new_severity,
            "blocked_entry": self._blocked_entry,
        }

    #rebuilds a review from its saved form, raises ValueError if the saved decision is not a known one
    @classmethod
    def from_dict(cls, data: dict) -> "AnalystReview":
        return cls(
            data.get("decision"),
            data.get("analyst", ""),
            data.get("reason", ""),
            data.get("reviewed_at", ""),
            data.get("previous_severity", ""),
            data.get("new_severity", ""),
            data.get("blocked_entry", ""),
        )

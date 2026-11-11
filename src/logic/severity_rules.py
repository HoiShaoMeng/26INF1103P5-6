"""severity_rules: the business rules that decide how serious a reported email is."""
from abc import ABC, abstractmethod
from enum import StrEnum


#the only three severities a report can get, listed lowest to highest so escalation can step up the list
#StrEnum: each member is also a normal string, so it still saves to reports.json as "CRITICAL" etc.
class Severity(StrEnum):
    LOG_ONLY = "LOG_ONLY"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CRITICAL = "CRITICAL"

    #returns the severity one tier higher, CRITICAL stays CRITICAL so it never goes out of bounds
    def escalate(self) -> "Severity":
        order = list(Severity)
        next_index = min(order.index(self) + 1, len(order) - 1)
        return order[next_index]


#abstract base class for every severity rule: a rule checks one condition and gives one severity if it matches.
#the classifier only talks to this base type, so a new rule can be added without changing the classifier.
class SeverityRule(ABC):

    def __init__(self, severity: Severity):
        #protected: subclasses set it once through super().__init__(), outside code can only read it
        self._severity = severity

    #read-only access to the severity this rule gives
    @property
    def severity(self) -> Severity:
        return self._severity

    #every subclass must decide when it matches, python will not create a subclass that skips this.
    #sender_email is optional: only rules that need the sender (e.g. the blocklist) use it, the others ignore it.
    @abstractmethod
    def matches(self, ai_output: dict, is_campaign: bool, sender_email: str = "") -> bool:
        pass

    #shared behaviour for all rules: gives this rule's severity if it matches, or None if it does not
    def apply(self, ai_output: dict, is_campaign: bool, sender_email: str = "") -> Severity | None:
        if self.matches(ai_output, is_campaign, sender_email):
            return self._severity
        return None


#fail-safe: if ai_manager could not get a real AI response it returns the AI_UNAVAILABLE placeholder.
#this must be checked first so a failed AI call is never mistaken for a safe email.
class AiUnavailableRule(SeverityRule):
    UNAVAILABLE_CLASSIFICATION = "AI_UNAVAILABLE"

    def __init__(self):
        super().__init__(Severity.NEEDS_REVIEW)

    def matches(self, ai_output: dict, is_campaign: bool, sender_email: str = "") -> bool:
        if not isinstance(ai_output, dict):
            return False
        return ai_output.get("classification") == self.UNAVAILABLE_CLASSIFICATION

#rule C: a detected campaign (3+ reports from the same sender/domain within 24h) is CRITICAL outright
#is_campaign comes from the campaign check, this rule only acts on the result
class CampaignRule(SeverityRule):

    def __init__(self):
        super().__init__(Severity.CRITICAL)

    def matches(self, ai_output: dict, is_campaign: bool, sender_email: str = "") -> bool:
        return bool(is_campaign)


#rule A: sender domain mismatch + real evidence (a suspicious link or attachment) is CRITICAL outright,
#no matter what threat_level the AI gave. this is the multi-condition rule using two AI fields.
class DomainMismatchEvidenceRule(SeverityRule):

    def __init__(self):
        super().__init__(Severity.CRITICAL)

    def matches(self, ai_output: dict, is_campaign: bool, sender_email: str = "") -> bool:
        sender_domain_mismatch = bool(ai_output.get("sender_domain_mismatch"))
        has_suspicious_urls = bool(ai_output.get("suspicious_urls"))
        has_suspicious_attachments = bool(ai_output.get("suspicious_attachments"))
        return sender_domain_mismatch and (has_suspicious_urls or has_suspicious_attachments)


#new feature: a sender an analyst already confirmed as phishing is CRITICAL straight away, even if the AI is down.
#association: the rule only refers to a Blocklist it is given, it does not create or own it.
class BlocklistRule(SeverityRule):

    def __init__(self, blocklist=None):
        super().__init__(Severity.CRITICAL)
        self._blocklist = blocklist

    def matches(self, ai_output: dict, is_campaign: bool, sender_email: str = "") -> bool:
        #no blocklist loaded means nothing is blocked, the other rules still run
        if self._blocklist is None:
            return False
        return self._blocklist.contains_sender(sender_email)


#new feature, safety net against missed phishing: if the AI flagged a link or attachment as suspicious,
#the report is never auto-archived as LOG_ONLY, even with a low threat_level. it goes to a person instead.
class SuspiciousEvidenceRule(SeverityRule):

    def __init__(self):
        super().__init__(Severity.NEEDS_REVIEW)

    def matches(self, ai_output: dict, is_campaign: bool, sender_email: str = "") -> bool:
        has_suspicious_urls = bool(ai_output.get("suspicious_urls"))
        has_suspicious_attachments = bool(ai_output.get("suspicious_attachments"))
        return has_suspicious_urls or has_suspicious_attachments


#base band: matches when the AI's threat_level is at or above min_level.
#one class, many objects: e.g. ThreatBandRule(80, CRITICAL) and ThreatBandRule(50, NEEDS_REVIEW)
class ThreatBandRule(SeverityRule):

    def __init__(self, min_level: int, severity: Severity):
        super().__init__(severity)
        self._min_level = min_level

    #read-only access to the lowest threat_level that matches this band
    @property
    def min_level(self) -> int:
        return self._min_level

    def matches(self, ai_output: dict, is_campaign: bool, sender_email: str = "") -> bool:
        threat_level = ai_output.get("threat_level")
        if not isinstance(threat_level, (int, float)):
            threat_level = 0  #missing/bad data should never crash the pipeline
        return threat_level >= self._min_level


#rule B: 2+ tactics detected together suggests a deliberate attack, so bump the severity up one tier.
#not a SeverityRule: it does not pick a severity, it adjusts one that a rule already picked.
class MultiTacticEscalation:

    def __init__(self, min_tactics: int = 2):
        self._min_tactics = min_tactics

    #read-only access to how many tactics are needed before escalating
    @property
    def min_tactics(self) -> int:
        return self._min_tactics

    def adjust(self, ai_output: dict, severity: Severity) -> Severity:
        tactics_detected = ai_output.get("tactics_detected") or []
        #Severity(...) also accepts a plain string like "NEEDS_REVIEW" and turns it into the enum member
        severity = Severity(severity)
        if len(tactics_detected) >= self._min_tactics:
            return severity.escalate()
        return severity

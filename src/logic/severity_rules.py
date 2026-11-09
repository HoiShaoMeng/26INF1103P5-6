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

    #every subclass must decide when it matches, python will not create a subclass that skips this
    @abstractmethod
    def matches(self, ai_output: dict, is_campaign: bool) -> bool:
        pass

    #shared behaviour for all rules: gives this rule's severity if it matches, or None if it does not
    def apply(self, ai_output: dict, is_campaign: bool) -> Severity | None:
        if self.matches(ai_output, is_campaign):
            return self._severity
        return None

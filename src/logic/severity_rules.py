"""severity_rules: the business rules that decide how serious a reported email is."""

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

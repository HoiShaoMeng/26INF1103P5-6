"""review_service: applies an analyst's decision to a saved report, the recovery step for missed phishing."""

from datetime import UTC, datetime
from typing import ClassVar

from analyst_review import AnalystReview, ReviewDecision
from blocklist import Blocklist
from screening_report import TriageDecision
from severity_rules import Severity


#turns an analyst's decision into a new severity, an audit record, a blocklist entry and re-checks.
#association: the recommender and blocklist are passed in and only referred to, this service does not own them.
class ReviewService:

    #the severity each analyst decision gives the report, shared by every ReviewService (ClassVar)
    DECISION_SEVERITY: ClassVar[dict] = {
        ReviewDecision.CONFIRMED_PHISHING: Severity.CRITICAL,
        ReviewDecision.CONFIRMED_SAFE: Severity.LOG_ONLY,
    }

    def __init__(self, action_recommender, blocklist: Blocklist):
        self._action_recommender = action_recommender
        self._blocklist = blocklist

    #applies the decision to the report and returns the review that was saved on it.
    #confirmed phishing also blocks the sender, so the next email from them is CRITICAL straight away.
    def apply_review(self, report, decision: ReviewDecision, analyst: str, reason: str,
                     reviewed_at: str | None = None):
        decision = ReviewDecision(decision)
        new_severity = self.DECISION_SEVERITY[decision]

        blocked_entry = ""
        if decision == ReviewDecision.CONFIRMED_PHISHING:
            blocked_entry = self._blocklist.block_sender(report.sender_email)

        review = AnalystReview(
            decision,
            analyst,
            reason,
            reviewed_at or datetime.now(UTC).isoformat(timespec="seconds"),
            report.severity,
            new_severity,
            blocked_entry,
        )
        report.apply_review(review, self._decision_for(new_severity, report.decision.is_campaign))
        return review

    #after a confirmed phishing: finds LOG_ONLY reports from the same attacker that were never reviewed,
    #sends them back to NEEDS_REVIEW and returns them. this answers "what else did we miss?".
    def flag_related(self, confirmed_report, history) -> list:
        attacker = Blocklist.entry_for(confirmed_report.sender_email)
        if not attacker:
            return []

        flagged = []
        for report in history.reports:
            is_same_report = report.report_id == confirmed_report.report_id
            is_same_attacker = Blocklist.entry_for(report.sender_email) == attacker
            was_archived = report.severity == Severity.LOG_ONLY and report.review is None
            if is_same_attacker and was_archived and not is_same_report:
                new_decision = self._decision_for(Severity.NEEDS_REVIEW, report.decision.is_campaign)
                report.flag_for_recheck(new_decision, confirmed_report.report_id)
                flagged.append(report)
        return flagged

    #private helper: builds a decision with the matching recommended action
    def _decision_for(self, severity: Severity, is_campaign: bool) -> TriageDecision:
        action = self._action_recommender.generate_recommended_action(severity)
        return TriageDecision(severity, is_campaign, action)

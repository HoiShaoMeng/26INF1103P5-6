from datetime import datetime, timedelta

from severity_rules import (
    AiUnavailableRule,
    BlocklistRule,
    CampaignRule,
    DomainMismatchEvidenceRule,
    Severity,
    SuspiciousEvidenceRule,
    ThreatBandRule,
)


#campaign detection: True = 3+ reports from the same sender/domain within 24 hours, treat as a coordinated attack.
#each report dict needs "sender_email" and "reported_at" (ISO format, e.g. 2026-09-25T14:00:00).
#the current report counts as 1, so 2 matching previous reports are needed to reach 3.
class CampaignDetector:
    def check_campaign(self, current_report: dict, previous_reports: list) -> bool:
        if not previous_reports:
            return False

        # Get the current sender email and normalise it by removing extra spaces and converting it to lowercase. 
        #Example: ATTACKER@fake.com and attacker@fake.com may otherwise be treated as different strings.
        current_sender = current_report["sender_email"].strip().lower()
        current_domain = current_sender.split("@")[1]
        current_time = datetime.fromisoformat(current_report["reported_at"])

        # Start at 1 because the current report itself counts as one report.
        match_count = 1

        # Compare the current report against all previous reports.
        for report in previous_reports:

            # Extract the previous report's sender, domain and time.
            # .strip().lower() ensures the comparison is not affected by spaces or capital letters.
            previous_sender = report["sender_email"].strip().lower()
            previous_domain = previous_sender.split("@")[1]
            previous_time = datetime.fromisoformat(report["reported_at"])

            # Check whether the exact sender email or the sender domain matches.
            same_sender = previous_sender == current_sender
            same_domain = previous_domain == current_domain

            if same_sender or same_domain:

                # Calculate how much earlier the previous report was submitted.
                time_difference = current_time - previous_time

                # Only count reports that happened within the previous 24 hours.
                # timedelta(0) also prevents future reports from being counted.
                if timedelta(0) <= time_difference <= timedelta(hours=24):
                    match_count += 1

                    # Stop checking once 3 related reports are found.
                    if match_count >= 3:
                        return True
        # If fewer than 3 related reports were found, no campaign is detected. 
        return False

#decides the severity for one AI-enriched report by running the severity rules in a fixed order.
#the rule order lives here in one place, so the order can be read and changed without touching any rule.
#association: the blocklist is only passed in and referred to, it is loaded and saved by the data layer.
class SeverityClassifier:

    def __init__(self, blocklist=None, critical_threshold: int = 80, needs_review_threshold: int = 50,
                 min_tactics: int = 2):
        #override rules: checked in order, the first one that matches decides the severity straight away
        self._override_rules = [
            BlocklistRule(blocklist),      #new: a sender already confirmed as phishing is always CRITICAL
            AiUnavailableRule(),           #fail-safe, so a failed AI call is never treated as safe
            CampaignRule(),                #rule C
            DomainMismatchEvidenceRule(),  #rule A
        ]
        #threat bands: highest band first, LOG_ONLY is the default when no band matches
        self._band_rules = [
            ThreatBandRule(critical_threshold, Severity.CRITICAL),
            ThreatBandRule(needs_review_threshold, Severity.NEEDS_REVIEW),
            SuspiciousEvidenceRule(),      #new safety net: flagged link/attachment is never LOG_ONLY
        ]
        #rule B: how many tactics at once count as a deliberate attack
        self._min_tactics = min_tactics

    def classify(self, ai_output: dict, is_campaign: bool = False, sender_email: str = "") -> Severity:
        #no AI output at all is treated like a failed AI call, it must never crash or be called safe
        if not isinstance(ai_output, dict):
            ai_output = {"classification": AiUnavailableRule.UNAVAILABLE_CLASSIFICATION}

        override = self._first_match(self._override_rules, ai_output, is_campaign, sender_email)
        if override is not None:
            return override

        severity = self._first_match(self._band_rules, ai_output, is_campaign, sender_email) or Severity.LOG_ONLY
        return self._escalate_for_tactics(ai_output, severity)

    #every rule is called through the same apply(), so this loop never changes when a rule is added
    #private helper: gives the severity of the first rule that matches, or None if none match
    def _first_match(self, rules: list, ai_output: dict, is_campaign: bool, sender_email: str) -> Severity | None:
        for rule in rules:
            severity = rule.apply(ai_output, is_campaign, sender_email)
            if severity is not None:
                return severity
        return None

    #rule B: 2+ tactics detected together suggests a deliberate attack, so bump the band result up one tier.
    #it is a step of the classifier, not a rule: it adjusts a severity a band already chose instead of choosing one.
    def _escalate_for_tactics(self, ai_output: dict, severity: Severity) -> Severity:
        tactics_detected = ai_output.get("tactics_detected") or []
        if len(tactics_detected) >= self._min_tactics:
            return Severity(severity).escalate()
        return Severity(severity)


# Generates the recommended action based on the final severity level.
# Each severity has a fixed action so the IT team knows what to do next.
class ActionRecommender:
    def generate_recommended_action(self, severity: str) -> str:
        
        # CRITICAL threats require immediate action:
        # block the sender domain and warn all users.
        if severity == Severity.CRITICAL:
            return "Block sender domain and alert all users."

        # NEEDS_REVIEW threats are suspicious but not urgent enough to block immediately,
        # so the IT team should manually review them within 24 hours.
        elif severity == Severity.NEEDS_REVIEW:
            return "Perform a manual check within 24 hours."

        # LOG_ONLY reports are low-risk, so they are archived
        # and no immediate action is required.
        elif severity == Severity.LOG_ONLY:
            return "Archive the report. No further action required."

        # Fallback for any unexpected severity value:
        # send it for manual review instead of taking an unsafe automatic action.
        return "Unknown severity. Manual review required."


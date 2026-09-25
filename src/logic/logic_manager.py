from datetime import datetime, timedelta

#Fail safe check: True if ai_manager cant get a real AI response and returned the AI_UNAVAILABLE placeholder instead.
#classify_severity() must run this first so a failed AI call never gets mistaken for a "safe" email.
def is_ai_unavailable(ai_output):

    if not isinstance(ai_output, dict):
        return False

    return ai_output.get("classification") == "AI_UNAVAILABLE"

#campaign detection: True = 3+ reports from the same sender/domain within 24 hours, treat as a coordinated attack.
#each report dict needs "sender_email" and "reported_at" (ISO format, e.g. 2026-09-25T14:00:00).
#the current report counts as 1, so 2 matching previous reports are needed to reach 3.
def check_campaign(current_report, previous_reports):
    current_sender = current_report["sender_email"]
    current_domain = current_sender.split("@")[1]
    current_time = datetime.fromisoformat(current_report["reported_at"])

    match_count = 1

    for report in previous_reports:
        previous_sender = report["sender_email"]
        previous_domain = previous_sender.split("@")[1]
        previous_time = datetime.fromisoformat(report["reported_at"])

        if previous_sender == current_sender or previous_domain == current_domain:
            time_difference = current_time - previous_time

            if timedelta(0) <= time_difference <= timedelta(hours=24):
                match_count += 1

    if match_count >= 3:
        return True

    return False

#threat_level band boundaries, this is the PRIMARY driver of severity, tactics never gate these bands
THREAT_LEVEL_CRITICAL_THRESHOLD = 80
THREAT_LEVEL_NEEDS_REVIEW_MIN = 50

#minimum number of distinct tactics detected at once before we treat it as a coordinated, deliberate attack
MULTI_TACTIC_ESCALATION_COUNT = 2

#the three possible outcomes classify_severity() can return, also used as an ordered scale for escalation
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_NEEDS_REVIEW = "NEEDS_REVIEW"
SEVERITY_LOG_ONLY = "LOG_ONLY"

#lets us bump a severity up by exactly one tier without a big if/elif chain
SEVERITY_ESCALATION_ORDER = [SEVERITY_LOG_ONLY, SEVERITY_NEEDS_REVIEW, SEVERITY_CRITICAL]

#bumps a severity one step up the scale, already-CRITICAL stays CRITICAL, doesnt go out of bounds
def _escalate_one_tier(severity):
    current_index = SEVERITY_ESCALATION_ORDER.index(severity)
    next_index = min(current_index + 1, len(SEVERITY_ESCALATION_ORDER) - 1)
    return SEVERITY_ESCALATION_ORDER[next_index]

#decides severity for one AI-enriched report.
#is_campaign is optional: pass True if check_campaign() already returned True for this report,
#leave it as the default False if there is no report history to compare against yet.
def classify_severity(ai_output, is_campaign=False):

    #fail-safe, always checked first, so a failed AI call never gets treated as safe
    if is_ai_unavailable(ai_output):
        return SEVERITY_NEEDS_REVIEW

    #rule C: a detected campaign (3+ reports from the same sender/domain within 24h) is CRITICAL outright,
    #regardless of threat_level, tactics, or anything else, per check_campaign()'s contract
    if is_campaign:
        return SEVERITY_CRITICAL

    tactics_detected = ai_output.get("tactics_detected") or []
    suspicious_urls = ai_output.get("suspicious_urls") or []
    suspicious_attachments = ai_output.get("suspicious_attachments") or []
    sender_domain_mismatch = bool(ai_output.get("sender_domain_mismatch"))

    threat_level = ai_output.get("threat_level")
    if not isinstance(threat_level, (int, float)):
        threat_level = 0  #missing/bad data should never crash the pipeline

    #rule A: domain mismatch + real evidence (a link or attachment) is CRITICAL outright, no matter what
    #the AI called the tactic, or what threat_level said, this combo alone is dangerous enough on its own
    has_suspicious_evidence = bool(suspicious_urls) or bool(suspicious_attachments)
    if sender_domain_mismatch and has_suspicious_evidence:
        return SEVERITY_CRITICAL

    #base severity comes from threat_level alone, this is the primary signal
    if threat_level >= THREAT_LEVEL_CRITICAL_THRESHOLD:
        severity = SEVERITY_CRITICAL
    elif threat_level >= THREAT_LEVEL_NEEDS_REVIEW_MIN:
        severity = SEVERITY_NEEDS_REVIEW
    else:
        severity = SEVERITY_LOG_ONLY

    #rule B: 2+ distinct tactics stacked together suggests a coordinated attack, escalate one tier as a safety net
    if len(tactics_detected) >= MULTI_TACTIC_ESCALATION_COUNT:
        severity = _escalate_one_tier(severity)

    return severity

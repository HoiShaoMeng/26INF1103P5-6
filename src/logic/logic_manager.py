#Fail safe check: True if ai_manager cant get a real AI response and returned the AI_UNAVAILABLE placeholder instead.
#classify_severity() must run this first so a failed AI call never gets mistaken for a "safe" email.
def is_ai_unavailable(ai_output):

    if not isinstance(ai_output, dict):
        return False

    return ai_output.get("classification") == "AI_UNAVAILABLE"

#threat_level band boundaries, this is the PRIMARY driver of severity
THREAT_LEVEL_CRITICAL_THRESHOLD = 80
THREAT_LEVEL_NEEDS_REVIEW_MIN = 50

SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_NEEDS_REVIEW = "NEEDS_REVIEW"
SEVERITY_LOG_ONLY = "LOG_ONLY"

#decides severity for one AI-enriched report
def classify_severity(ai_output):

    #fail-safe, always checked first, so a failed AI call never gets treated as safe
    if is_ai_unavailable(ai_output):
        return SEVERITY_NEEDS_REVIEW

    suspicious_urls = ai_output.get("suspicious_urls") or []
    suspicious_attachments = ai_output.get("suspicious_attachments") or []
    sender_domain_mismatch = bool(ai_output.get("sender_domain_mismatch"))

    threat_level = ai_output.get("threat_level")
    if not isinstance(threat_level, (int, float)):
        threat_level = 0  #missing/bad data should never crash the pipeline

    #rule A: domain mismatch + real evidence (a link or attachment) is CRITICAL outright, regardless of threat_level
    has_suspicious_evidence = bool(suspicious_urls) or bool(suspicious_attachments)
    if sender_domain_mismatch and has_suspicious_evidence:
        return SEVERITY_CRITICAL

    #base severity comes from threat_level alone, this is the primary signal
    if threat_level >= THREAT_LEVEL_CRITICAL_THRESHOLD:
        return SEVERITY_CRITICAL
    elif threat_level >= THREAT_LEVEL_NEEDS_REVIEW_MIN:
        return SEVERITY_NEEDS_REVIEW
    return SEVERITY_LOG_ONLY

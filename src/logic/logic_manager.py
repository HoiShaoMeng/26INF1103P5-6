"""
logic_manager.py

Logic Manager (domain layer) for the Phishing/Suspicious Email Triage
Assistant.

Responsibilities:
    - Apply business rules to the AI-enriched record produced by
      ai_manager and decide a severity outcome.

Constraints (per project architecture):
    - 100% procedural: functions only, no classes.
    - Never calls the AI API.
    - Never uses print() or input().
    - Never touches files directly.
    - Pure functions operating on dicts (and other plain data
      structures) passed in by the caller.

Expected ai_output dict fields (produced by ai_manager, confirmed
against ai_manager.py before use):
    classification              (str)  e.g. "AI_UNAVAILABLE" on failure
    confidence                  (int/float)
    tactics_detected            (list[str])
    suspicious_urls             (list[str])
    suspicious_attachments      (list[str])
    sender_domain_mismatch      (bool)
"""


def is_ai_unavailable(ai_output):
    """
    Determine whether the AI enrichment step failed to produce a real
    result.

    ai_manager is expected to hand back a record with
    classification == "AI_UNAVAILABLE" (instead of a normal
    classification such as "phishing" / "spam" / "benign") whenever it
    could not get a usable response from the AI API. This function is
    the fail-safe check that lets classify_severity() short-circuit
    before running any other business rule.

    Args:
        ai_output (dict): The AI-enriched record. Expected to contain
            a "classification" key, but this function tolerates a
            missing key rather than raising.

    Returns:
        bool: True if the AI output indicates the AI was unavailable,
            False otherwise (including when ai_output is malformed).
    """
    if not isinstance(ai_output, dict):
        return False

    return ai_output.get("classification") == "AI_UNAVAILABLE"

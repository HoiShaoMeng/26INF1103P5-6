"""Unit tests for severity_rules: every ai_output below is a fake dict, so no AI API calls are made."""

import os
import sys

import pytest

# adds the src/logic folder to the path so we can import severity_rules.py for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "logic"))

from severity_rules import (  # type: ignore
    AiUnavailableRule,
    CampaignRule,
    DomainMismatchEvidenceRule,
    MultiTacticEscalation,
    Severity,
    SeverityRule,
    ThreatBandRule,
)

# --- Severity ---
def test_severity_values_are_the_saved_strings():
    assert Severity.CRITICAL == "CRITICAL"
    assert Severity.NEEDS_REVIEW == "NEEDS_REVIEW"
    assert Severity.LOG_ONLY == "LOG_ONLY"

def test_severity_escalates_one_tier_and_stops_at_critical():
    assert Severity.LOG_ONLY.escalate() == Severity.NEEDS_REVIEW
    assert Severity.NEEDS_REVIEW.escalate() == Severity.CRITICAL
    assert Severity.CRITICAL.escalate() == Severity.CRITICAL

# --- SeverityRule (abstract base class) ---
def test_severity_rule_cannot_be_created_directly():
    with pytest.raises(TypeError):
        SeverityRule(Severity.CRITICAL)

def test_every_rule_is_a_severity_rule():
    rules = [AiUnavailableRule(), CampaignRule(), DomainMismatchEvidenceRule(),
             ThreatBandRule(80, Severity.CRITICAL)]
    for rule in rules:
        assert isinstance(rule, SeverityRule)

def test_apply_gives_severity_on_match_and_none_otherwise():
    rule = CampaignRule()
    assert rule.apply({}, is_campaign=True) == Severity.CRITICAL
    assert rule.apply({}, is_campaign=False) is None

# --- AiUnavailableRule ---
def test_ai_unavailable_rule_matches_placeholder():
    rule = AiUnavailableRule()
    assert rule.matches({"classification": "AI_UNAVAILABLE"}, False) is True
    assert rule.severity == Severity.NEEDS_REVIEW

def test_ai_unavailable_rule_ignores_normal_classification_and_non_dict():
    rule = AiUnavailableRule()
    assert rule.matches({"classification": "phishing"}, False) is False
    assert rule.matches(None, False) is False

# --- CampaignRule ---
def test_campaign_rule_follows_is_campaign():
    rule = CampaignRule()
    assert rule.matches({"threat_level": 0}, True) is True
    assert rule.matches({"threat_level": 100}, False) is False

# --- DomainMismatchEvidenceRule (rule A) ---
@pytest.mark.parametrize("ai_output, expected", [
    ({"sender_domain_mismatch": True, "suspicious_urls": ["http://x.com"]}, True),
    ({"sender_domain_mismatch": True, "suspicious_attachments": ["a.exe"]}, True),
    ({"sender_domain_mismatch": True, "suspicious_urls": [], "suspicious_attachments": []}, False),
    ({"sender_domain_mismatch": False, "suspicious_urls": ["http://x.com"]}, False),
])
def test_domain_mismatch_rule_needs_mismatch_and_evidence(ai_output, expected):
    assert DomainMismatchEvidenceRule().matches(ai_output, False) is expected

# --- ThreatBandRule ---
@pytest.mark.parametrize("threat_level, expected", [(80, True), (79, False), (100, True)])
def test_critical_band_boundary(threat_level, expected):
    rule = ThreatBandRule(80, Severity.CRITICAL)
    assert rule.matches({"threat_level": threat_level}, False) is expected

@pytest.mark.parametrize("threat_level, expected", [(50, True), (49, False)])
def test_needs_review_band_boundary(threat_level, expected):
    rule = ThreatBandRule(50, Severity.NEEDS_REVIEW)
    assert rule.matches({"threat_level": threat_level}, False) is expected

def test_threat_band_treats_missing_or_bad_threat_level_as_zero():
    rule = ThreatBandRule(50, Severity.NEEDS_REVIEW)
    assert rule.matches({}, False) is False
    assert rule.matches({"threat_level": "high"}, False) is False
    assert rule.min_level == 50

# --- MultiTacticEscalation (rule B) ---
def test_two_tactics_escalate_one_tier():
    escalation = MultiTacticEscalation()
    ai_output = {"tactics_detected": ["impersonation", "urgency_pressure"]}
    assert escalation.adjust(ai_output, Severity.LOG_ONLY) == Severity.NEEDS_REVIEW
    assert escalation.adjust(ai_output, Severity.NEEDS_REVIEW) == Severity.CRITICAL
    assert escalation.adjust(ai_output, Severity.CRITICAL) == Severity.CRITICAL

def test_one_or_no_tactics_do_not_escalate():
    escalation = MultiTacticEscalation()
    assert escalation.adjust({"tactics_detected": ["impersonation"]}, Severity.LOG_ONLY) == Severity.LOG_ONLY
    assert escalation.adjust({}, Severity.NEEDS_REVIEW) == Severity.NEEDS_REVIEW

def test_escalation_accepts_a_plain_severity_string():
    escalation = MultiTacticEscalation()
    ai_output = {"tactics_detected": ["impersonation", "urgency_pressure"]}
    assert escalation.adjust(ai_output, "NEEDS_REVIEW") == Severity.CRITICAL

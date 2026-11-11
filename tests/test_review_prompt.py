"""Unit tests for ReviewPrompt: the typed answers are faked, so no keyboard is needed."""

import os
import sys

# adds the src/io and src/domain folders to the path so we can import the classes for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "io"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "domain"))

from analyst_review import AnalystReview, ReviewDecision  # type: ignore
from review_prompt import ReviewPrompt  # type: ignore


# builds a prompt that "types" the given answers in order, and collects its error messages
def make_prompt(answers):
    typed = iter(answers)
    errors = []
    return ReviewPrompt(lambda prompt: next(typed), errors.append), errors


def test_report_number_re_prompts_until_in_range():
    prompt, errors = make_prompt(["0", "abc", "4", "2"])
    assert prompt.ask_report_number(3) == 1
    assert len(errors) == 3


def test_decision_choices():
    assert make_prompt(["1"])[0].ask_decision() == ReviewDecision.CONFIRMED_PHISHING
    assert make_prompt(["2"])[0].ask_decision() == ReviewDecision.CONFIRMED_SAFE
    assert make_prompt(["3"])[0].ask_decision() is None


def test_text_is_required_and_has_a_maximum_length():
    prompt, errors = make_prompt(["", "x" * 201, "  Shao  "])
    assert prompt.ask_text("Analyst name") == "Shao"
    assert errors == ["Analyst name is required.", "Analyst name is too long (max 200 characters)."]


def test_result_lines_show_severity_change_blocklist_and_rechecks():
    review = AnalystReview(ReviewDecision.CONFIRMED_PHISHING, "Shao", "fake login", "2026-11-11T03:00:00+00:00",
                           "LOG_ONLY", "CRITICAL", "evil.com")
    lines = make_prompt([])[0].build_result_lines("abc12345", review, 2)
    text = "\n".join(lines)
    assert "LOG_ONLY -> CRITICAL" in text
    assert "evil.com" in text
    assert "2 related LOG_ONLY report(s)" in text


def test_result_lines_for_a_safe_review_have_no_block_or_recheck():
    review = AnalystReview(ReviewDecision.CONFIRMED_SAFE, "Shao", "real newsletter", "2026-11-11T03:00:00+00:00",
                           "NEEDS_REVIEW", "LOG_ONLY")
    text = "\n".join(make_prompt([])[0].build_result_lines("abc12345", review, 0))
    assert "Blocked" not in text
    assert "Re-check" not in text

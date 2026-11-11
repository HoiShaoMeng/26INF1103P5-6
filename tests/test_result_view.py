"""Unit tests for ResultView and its TextView base: printed lines are collected in a list."""

import os
import sys

import pytest

# adds the src/io folder to the path so we can import result_view.py and text_view.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "io"))

from result_view import ResultView  # type: ignore
from text_view import TextView  # type: ignore

RECORD = {"sender_email": "alerts@paypa1.com", "sender_name": "PayPal",
          "subject": "Blocked funds", "reported_at": "2026-11-12T08:30:00+00:00"}
AI_RESULT = {"classification": "PHISHING", "threat_level": 92}


# builds a view that collects every printed line in a list
def make_view():
    lines = []
    return ResultView(lines.append), lines


def test_result_is_boxed_with_a_title():
    lines = ResultView().build_lines(RECORD, AI_RESULT, "CRITICAL", "Block the sender")
    assert lines[1] == "SCREENING RESULT"
    assert lines[0] == lines[2] == lines[-1] == "=" * len(lines[0])


def test_every_field_is_shown():
    text = "\n".join(ResultView().build_lines(RECORD, AI_RESULT, "CRITICAL", "Block the sender", True))
    for expected in ["PayPal <alerts@paypa1.com>", "Blocked funds", "PHISHING", "92",
                     "Campaign:", "YES", "CRITICAL", "Block the sender"]:
        assert expected in text


def test_any_ai_field_name_is_shown():
    text = "\n".join(ResultView().build_lines(RECORD, {"new_field": "x"}, "LOG_ONLY", "Log it"))
    assert "New field:" in text


def test_missing_ai_result_shows_unknown():
    lines = ResultView().build_lines(RECORD, None, "NEEDS_REVIEW", "Check manually")
    assert any(line.startswith("Ai result:") and line.endswith("unknown") for line in lines)


def test_values_start_in_the_same_column():
    lines = ResultView().build_lines(RECORD, AI_RESULT, "CRITICAL", "Block the sender")
    field_lines = [line for line in lines if ":" in line and not line.startswith(("=", "-"))]
    columns = {len(line) - len(line.split(":", 1)[1].lstrip()) for line in field_lines}
    assert len(columns) == 1


def test_show_prints_a_blank_line_then_the_result():
    view, lines = make_view()
    view.show(RECORD, AI_RESULT, "CRITICAL", "Block the sender")
    assert lines[0] == ""
    assert lines[1:] == view.build_lines(RECORD, AI_RESULT, "CRITICAL", "Block the sender")


def test_text_view_cannot_be_created_on_its_own():
    with pytest.raises(TypeError):
        TextView()


@pytest.mark.parametrize("value, expected", [
    (None, "unknown"), (True, "YES"), (False, "no"), ([], "none"),
    (["a", "b"], "a, b"), ({"x": 1, "y": None}, "1, unknown"), (7, "7"),
])
def test_values_are_formatted_by_type(value, expected):
    assert TextView.format_value(value) == expected
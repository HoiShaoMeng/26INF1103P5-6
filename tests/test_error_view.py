"""Unit tests for ErrorView: printed lines are collected in a list, so nothing goes to the screen."""

import os
import sys

# adds the src/io folder to the path so we can import error_view.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "io"))

from error_view import ErrorView  # type: ignore


# builds a view that collects every printed line in a list
def make_view():
    lines = []
    return ErrorView(lines.append), lines


def test_message_names_the_source_and_problem():
    assert ErrorView.format_message("AI", "request timed out") == "  [!] AI error: request timed out."


def test_next_step_is_added_after_the_problem():
    message = ErrorView.format_message("AI", "request timed out", "Perform a manual check within 24 hours.")
    assert message == "  [!] AI error: request timed out. Perform a manual check within 24 hours."


def test_full_stop_is_not_doubled():
    assert ErrorView.format_message("Data", "file is locked.") == "  [!] Data error: file is locked."


def test_exception_can_be_the_problem():
    assert ErrorView.format_message("Data", ValueError("bad JSON")) == "  [!] Data error: bad JSON."


def test_input_error_has_the_prefix_only():
    assert ErrorView.format_input_error("Subject is required.") == "  [!] Subject is required."


def test_show_prints_one_line():
    view, lines = make_view()
    view.show("Data", "the report could not be saved")
    assert lines == ["  [!] Data error: the report could not be saved."]


def test_show_input_error_prints_one_line():
    view, lines = make_view()
    view.show_input_error("Please enter y or n.")
    assert lines == ["  [!] Please enter y or n."]
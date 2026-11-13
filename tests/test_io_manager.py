import os
import sys

# adds the src/io and src/domain folders to the path so we can import io_manager.py and the classes it uses
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "io"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "domain"))

import io_manager  # type: ignore
from io_manager import IOManager  # type: ignore

RECORD = {"sender_email": "alerts@paypa1.com", "sender_name": "PayPal", "subject": "Blocked funds",
          "body": "Verify now.", "urls": [], "attachments": [], "reported_at": "2026-11-13T08:30:00+00:00"}


# builds a manager that "types" the given lines in order, and collects the lines the views print
def make_manager(*typed):
    answers = iter(typed)
    lines = []
    return IOManager(read_input=lambda prompt: next(answers), print_line=lines.append), lines


def test_menu_choice_returns_the_number():
    manager, _ = make_manager("2")
    assert manager.prompt_menu_choice() == "2"


def test_invalid_menu_choice_is_asked_again(capsys):
    manager, _ = make_manager("9", " 3 ")
    assert manager.prompt_menu_choice() == "3"
    assert "[!]" in capsys.readouterr().out


def test_severity_choice_returns_the_saved_form():
    manager, _ = make_manager("2")
    assert manager.prompt_severity_choice() == "NEEDS_REVIEW"


def test_email_fields_are_collected_into_one_record():
    manager, _ = make_manager("alerts@paypa1.com", "PayPal", "Blocked funds", "Verify now.", "END", "n", "n")
    record = manager.prompt_email_fields()
    assert record["sender_email"] == "alerts@paypa1.com"
    assert record["body"] == "Verify now."
    assert record["urls"] == [] and record["attachments"] == []


def test_ai_input_leaves_out_the_report_time():
    ai_input = IOManager.get_ai_input(RECORD)
    assert "reported_at" not in ai_input
    assert ai_input["subject"] == "Blocked funds"


def test_screening_result_is_printed_through_the_view():
    manager, lines = make_manager()
    manager.display_screening_result(RECORD, {"classification": "phishing"}, "CRITICAL", "Block the sender")
    assert "SCREENING RESULT" in lines


def test_report_list_is_printed_through_the_view():
    manager, lines = make_manager()
    manager.display_report_list([], "CRITICAL")
    assert " No CRITICAL reports saved yet." in lines


def test_error_is_shown_with_the_prefix(capsys):
    manager, _ = make_manager()
    manager.display_error("AI", "request timed out", "Retrying...")
    assert "[!] AI error: request timed out. Retrying..." in capsys.readouterr().out


def test_run_with_loading_returns_the_task_result():
    manager, _ = make_manager()
    assert manager.run_with_loading("Working", lambda a, b: a + b, 2, 3) == 5


def test_bridge_names_still_work_for_existing_callers():
    assert io_manager.get_ai_input(RECORD) == IOManager.get_ai_input(RECORD)
    assert io_manager.MENU_OPTIONS is IOManager.MENU_OPTIONS
    assert callable(io_manager.display_error)
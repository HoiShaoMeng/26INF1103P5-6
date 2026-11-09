"""Unit tests for MenuPrompt: the typed answers are faked, so no keyboard is needed."""

import os
import sys

# adds the src/io folder to the path so we can import menu_prompt.py for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "io"))

from menu_prompt import MenuPrompt  # type: ignore

OPTIONS = {"1": "First", "2": "Second", "3": "Third"}


# builds a menu that "types" the given answers in order, and collects its error messages
def make_menu(answers, options=OPTIONS):
    typed = iter(answers)
    errors = []
    menu = MenuPrompt("Test menu", options, lambda prompt: next(typed), errors.append)
    return menu, errors


def test_valid_choice_returns_its_number():
    menu, errors = make_menu(["2"])
    assert menu.ask() == "2"
    assert errors == []


def test_ask_label_returns_the_option_text():
    menu, _ = make_menu(["3"])
    assert menu.ask_label() == "Third"


def test_invalid_choice_is_asked_again():
    menu, errors = make_menu(["9", "1"])
    assert menu.ask() == "1"
    assert errors == ["Please enter one of: 1, 2, 3."]


def test_blank_choice_is_asked_again():
    menu, errors = make_menu(["", "2"])
    assert menu.ask() == "2"
    assert len(errors) == 1


def test_every_invalid_choice_gets_one_error():
    menu, errors = make_menu(["a", "0", "first", "3"])
    assert menu.ask() == "3"
    assert len(errors) == 3


def test_title_and_options_are_printed(capsys):
    menu, _ = make_menu(["1"])
    menu.ask()
    printed = capsys.readouterr().out
    assert "=== Test menu ===" in printed
    assert "  2. Second" in printed


def test_menu_is_printed_only_once_when_re_asking(capsys):
    menu, _ = make_menu(["x", "y", "1"])
    menu.ask()
    assert capsys.readouterr().out.count("=== Test menu ===") == 1


def test_options_come_from_the_caller():
    menu, errors = make_menu(["1", "7"], {"7": "Only option"})
    assert menu.ask_label() == "Only option"
    assert errors == ["Please enter one of: 7."]
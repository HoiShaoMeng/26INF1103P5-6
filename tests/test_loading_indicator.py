"""Unit tests for LoadingIndicator: output goes to a fake terminal, so nothing is printed on screen."""

import os
import sys
import threading
import time

import pytest

# adds the src/io folder to the path so we can import loading_indicator.py for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "io"))

from loading_indicator import LoadingIndicator  # type: ignore


# stands in for the screen: keeps everything written to it, and says whether it is a real terminal
class FakeTerminal:
    def __init__(self, is_terminal: bool):
        self.text = ""
        self._is_terminal = is_terminal

    def write(self, text: str) -> int:
        self.text += text
        return len(text)

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        return self._is_terminal


def slow_task(result, seconds=0.05):
    time.sleep(seconds)
    return result


def test_run_returns_the_task_result():
    indicator = LoadingIndicator(interval=0.01, output=FakeTerminal(True))
    assert indicator.run("Working", slow_task, 42) == 42


def test_dots_are_shown_then_cleared_in_a_terminal():
    terminal = FakeTerminal(True)
    LoadingIndicator(interval=0.01, output=terminal).run("Working", slow_task, "done")
    assert "\rWorking." in terminal.text
    assert "\rWorking..." in terminal.text
    # the last thing written wipes the line, so the next output starts clean
    assert terminal.text.endswith("\r")


def test_message_is_printed_once_when_not_a_terminal():
    terminal = FakeTerminal(False)
    result = LoadingIndicator(interval=0.01, output=terminal).run("Working", slow_task, "done")
    assert result == "done"
    assert terminal.text == "Working...\n"


def test_dots_stop_even_if_the_task_fails():
    terminal = FakeTerminal(True)
    indicator = LoadingIndicator(interval=0.01, output=terminal)
    threads_before = threading.active_count()

    def failing_task():
        time.sleep(0.03)
        raise ValueError("AI request failed")

    with pytest.raises(ValueError):
        indicator.run("Working", failing_task)
    assert threading.active_count() == threads_before
    assert terminal.text.endswith("\r")


def test_message_during_loading_gets_its_own_line():
    terminal = FakeTerminal(True)
    indicator = LoadingIndicator(interval=0.01, output=terminal)

    def task_that_reports_an_error():
        time.sleep(0.03)
        indicator.print_message("[!] Retrying")
        time.sleep(0.03)

    indicator.run("Working", task_that_reports_an_error)
    # the dots line is wiped (ends in \r) before the message is printed
    assert "\r[!] Retrying\n" in terminal.text


def test_print_message_without_loading_just_prints():
    terminal = FakeTerminal(True)
    LoadingIndicator(output=terminal).print_message("[!] Bad input")
    assert terminal.text == "[!] Bad input\n"
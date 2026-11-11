"""review_prompt: the terminal questions and result screen for reviewing a saved report."""

from collections.abc import Callable
from typing import ClassVar

from analyst_review import ReviewDecision
from menu_prompt import MenuPrompt


#asks which report to review, the analyst's decision, their name and reason, then shows what changed.
#how it reads input and reports errors is passed in, the same as MenuPrompt, so tests can fake the typing.
class ReviewPrompt:

    #the numbered choices shown to the analyst, shared by every ReviewPrompt (ClassVar)
    DECISION_OPTIONS: ClassVar[dict] = {"1": "Confirmed phishing (block sender)",
                                        "2": "Confirmed safe (false alarm)", "3": "Cancel"}
    MAX_TEXT_LENGTH = 200

    def __init__(self, read_input: Callable[[str], str], show_error: Callable[[str], None]):
        self._read_input = read_input
        self._show_error = show_error

    #asks for a report number from the list on screen and returns its position (0 for [1]), re-prompts until valid
    def ask_report_number(self, count: int) -> int:
        while True:
            answer = self._read_input(f"Report number to review (1-{count}): ").strip()
            if answer.isdigit() and 1 <= int(answer) <= count:
                return int(answer) - 1
            self._show_error(f"Please enter a number from 1 to {count}.")

    #returns the chosen ReviewDecision, or None if the analyst chose Cancel
    def ask_decision(self) -> ReviewDecision | None:
        choice = MenuPrompt("Analyst decision", self.DECISION_OPTIONS, self._read_input, self._show_error).ask()
        if choice == "1":
            return ReviewDecision.CONFIRMED_PHISHING
        if choice == "2":
            return ReviewDecision.CONFIRMED_SAFE
        return None

    #asks for required text (analyst name, reason), re-prompts on empty or too long answers
    def ask_text(self, label: str) -> str:
        while True:
            answer = self._read_input(f"{label}: ").strip()
            if not answer:
                self._show_error(f"{label} is required.")
            elif len(answer) > self.MAX_TEXT_LENGTH:
                self._show_error(f"{label} is too long (max {self.MAX_TEXT_LENGTH} characters).")
            else:
                return answer

    #builds the result screen lines (no printing), so it can be tested
    def build_result_lines(self, report_id: str, review, flagged_count: int) -> list[str]:
        lines = [
            "=" * 64,
            " REVIEW SAVED",
            "=" * 64,
            f" Report:        {report_id}",
            f" Decision:      {review.decision.replace('_', ' ').lower()}",
            f" Severity:      {review.previous_severity} -> {review.new_severity}",
            f" Reviewed by:   {review.analyst}",
            f" Reason:        {review.reason}",
        ]
        if review.blocked_entry:
            lines.append(f" Blocked:       {review.blocked_entry} (future emails are CRITICAL)")
        if flagged_count:
            lines.append(f" Re-check:      {flagged_count} related LOG_ONLY report(s) moved to NEEDS_REVIEW")
        lines.append("=" * 64)
        return lines

    #prints the result screen
    def show_result(self, report_id: str, review, flagged_count: int) -> None:
        print()
        for line in self.build_result_lines(report_id, review, flagged_count):
            print(line)

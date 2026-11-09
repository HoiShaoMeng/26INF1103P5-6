"""menu_prompt: shows a numbered list of options and asks the user to pick one."""

from collections.abc import Callable


class MenuPrompt:
    """One numbered menu. How it reads input and reports errors is passed in, so tests can fake the typing."""

    def __init__(self, title: str, options: dict[str, str],
                 read_input: Callable[[str], str], show_error: Callable[[str], None]):
        self._title = title
        self._options = options
        self._read_input = read_input
        self._show_error = show_error

    def _display(self) -> None:
        """Prints the title and the numbered options."""
        print()
        print(f"=== {self._title} ===")
        for number, label in self._options.items():
            print(f"  {number}. {label}")

    def ask(self) -> str:
        """Shows the menu and re-prompts until the user picks an option. Returns its number, e.g. '2'."""
        self._display()
        while True:
            choice = self._read_input("Choose an option: ")
            if choice in self._options:
                return choice
            self._show_error(f"Please enter one of: {', '.join(self._options)}.")

    def ask_label(self) -> str:
        """Same as ask(), but returns the option's text, e.g. 'NEEDS_REVIEW'."""
        return self._options[self.ask()]
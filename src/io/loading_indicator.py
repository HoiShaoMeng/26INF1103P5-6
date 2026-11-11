"""loading_indicator: shows animated dots while a slow task (like the AI request) runs."""

import sys
import threading


class LoadingIndicator:
    """Shows 'message.', 'message..', 'message...' on one line in a background thread while a task runs."""

    def __init__(self, interval: float = 0.4, output=None):
        self._interval = interval
        self._output = output if output is not None else sys.stdout
        # How wide the dots line on screen is (0 = nothing shown).
        self._width = 0
        # Stops the dots thread and another message from printing at the same moment.
        self._lock = threading.Lock()

    def _clear_line(self) -> None:
        """Wipes the dots line so the next output starts on a clean line. The caller must hold the lock."""
        if self._width:
            # \r jumps back to the start of the line; the spaces overwrite the old dots.
            print("\r" + " " * self._width + "\r", end="", flush=True, file=self._output)
            self._width = 0

    def _animate(self, message: str, stop: threading.Event) -> None:
        """Redraws the dots until stop is set. Runs in the background thread."""
        dots = 1
        while True:
            # :<3 pads to 3 characters, so going from "..." back to "." leaves no leftover dots.
            line = f"{message}{'.' * dots:<3}"
            with self._lock:
                print("\r" + line, end="", flush=True, file=self._output)
                self._width = len(line)
            if stop.wait(self._interval):
                break
            # Cycles 1 -> 2 -> 3 -> 1 ...
            dots = dots % 3 + 1
        with self._lock:
            self._clear_line()

    def print_message(self, text: str) -> None:
        """Prints a line without mixing it into the dots, e.g. an error shown while the AI is retrying."""
        with self._lock:
            self._clear_line()
            print(text, file=self._output)

    def run(self, message: str, task, *args):
        """Runs task(*args) while the dots show it is busy, then returns the task's result."""
        # Not a real terminal (e.g. output piped to a file): print once, as \r would leave a mess.
        if not self._output.isatty():
            print(f"{message}...", file=self._output)
            return task(*args)
        stop = threading.Event()
        dots_thread = threading.Thread(target=self._animate, args=(message, stop), daemon=True)
        dots_thread.start()
        try:
            return task(*args)
        finally:
            # Runs even if the task fails, so the dots never keep going.
            stop.set()
            dots_thread.join()
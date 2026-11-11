"""atomic_json_writer: writes JSON so a crash half way never damages the file already on disk."""

import json
import os
from pathlib import Path


#writes data to a temp file first and only swaps it in once it is complete,
#so the old file is either fully replaced or left untouched, never half written.
class AtomicJsonWriter:

    #returns True when the file was written, False when it failed (no print here, io shows the message)
    def write(self, file_path: Path, data) -> bool:
        file_path = Path(file_path)
        temp_path = file_path.with_name(file_path.name + ".tmp")

        try:
            #make sure the data folder exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)

            #only once the temp file is complete, swap it in as the real file
            os.replace(temp_path, file_path)
            return True

        except (OSError, TypeError, ValueError):
            #OSError: no permission, disk full, folder cant be created. TypeError/ValueError: data cant be turned into JSON
            #remove the half written temp file, the old file is left untouched
            self._remove_quietly(temp_path)
            return False

    #private helper: deletes the temp file if it exists, ignores errors because the save already failed
    @staticmethod
    def _remove_quietly(path: Path) -> None:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass

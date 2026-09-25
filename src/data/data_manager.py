import json
from pathlib import Path


def read_file():
    current_file = Path(__file__)
    project_dir = current_file.parent.parent.parent
    file_path = project_dir / "data" / "reports.json"

    try:
        with open(file_path, "r") as file:
            data = json.load(file)

        return data

    except FileNotFoundError:
        return []

    except json.JSONDecodeError:
        print("Something went wrong reading the reports.")
        return []


if __name__ == "__main__":
    print(read_file())
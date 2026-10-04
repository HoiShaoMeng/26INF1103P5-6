import json
from pathlib import Path


def read_file():
    #Locate reports.json relative to this python file,
    #so the program works regardless of the current working directory
    current_file = Path(__file__)
    project_dir = current_file.parent.parent.parent
    file_path = project_dir / "data" / "reports.json"

    try:
        #Read and convert the JSON file into python data
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Ensure the report history is stored as a list.
        if not isinstance(data, list):
            print("Reports file has an invalid format.")
            return []

        return data

    except FileNotFoundError:
        # No existing reports means the report history starts empty.
        return []

    except json.JSONDecodeError:
        #Prevent the program from crashing if the JSON file is corrupted/invalid
        print("Invalid JSON format in reports file.")
        return []


if __name__ == "__main__":
    # Run this test only when this file is executed directly.
    print(read_file())
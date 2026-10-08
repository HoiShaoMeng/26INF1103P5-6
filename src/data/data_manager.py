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

#builds the one flat record that gets saved to reports.json, it only arranges data and never decides anything.
#sender_email and reported_at stay at the top level because check_campaign() reads them from the saved reports.
#returns an empty dict if the record is missing either of them, so a report that campaign detection cant use is never saved.
def format_report(record: dict, ai_output: dict, is_campaign: bool, severity: str, recommended_action: str) -> dict:

    if not isinstance(record, dict):
        return {}

    if "sender_email" not in record or "reported_at" not in record:
        return {}

    #ai_output is not a dict if the AI failed, so fall back to an empty dict instead of crashing
    if not isinstance(ai_output, dict):
        ai_output = {}

    return {
        #fields from io_manager
        "sender_email": record["sender_email"],
        "sender_name": record.get("sender_name", ""),
        "subject": record.get("subject", ""),
        "body": record.get("body", ""),
        "urls": record.get("urls") or [],
        "attachments": record.get("attachments") or [],
        "reported_at": record["reported_at"],

        #fields from ai_manager
        "classification": ai_output.get("classification"),
        "threat_level": ai_output.get("threat_level"),
        "tactics_detected": ai_output.get("tactics_detected") or [],
        "suspicious_urls": ai_output.get("suspicious_urls") or [],
        "suspicious_attachments": ai_output.get("suspicious_attachments") or [],
        "sender_domain_mismatch": ai_output.get("sender_domain_mismatch"),

        #fields from logic_manager
        "is_campaign": is_campaign,
        "severity": severity,
        "recommended_action": recommended_action,
    }

#saves the whole report history to data/reports.json, the same file read_file() reads.
#order in the pipeline: read_file() -> add the new report to the list -> write_file(list)
#returns True when the file was written, False when it failed (no print here, io_manager shows the message).
def write_file(reports: list) -> bool:
    #read_file() only accepts a list, so never write anything else
    if not isinstance(reports, list):
        return False

    #locate reports.json the same way read_file() does
    current_file = Path(__file__)
    project_dir = current_file.parent.parent.parent
    file_path = project_dir / "data" / "reports.json"
    temp_path = project_dir / "data" / "reports.json.tmp"

    try:
        #make sure the data folder exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        #write to a temp file first, so a crash half way never damages the real history
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(reports, file, indent=2, ensure_ascii=False)
            file.write("")

        #only once the temp file is complete, swap it in as the real file
        os.replace(temp_path, file_path)
        return True
    
if __name__ == "__main__":
    # Run this test only when this file is executed directly.
    print(read_file())
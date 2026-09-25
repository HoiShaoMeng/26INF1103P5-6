from datetime import datetime, timedelta

#fail safe check: True if ai_manager cant get a real AI response and returned the AI_UNAVAILABLE placeholder instead. 
#classify_severity() must run this first so a failed AI call never gets mistaken for a "safe" email.
def is_ai_unavailable(ai_output):

    if not isinstance(ai_output, dict):
        return False

    return ai_output.get("classification") == "AI_UNAVAILABLE"


def check_campaign(current_report, previous_reports):
    current_sender = current_report["sender_email"]
    current_domain = current_sender.split("@")[1]
    current_time = datetime.fromisoformat(current_report["reported_at"])

    match_count = 1

    for report in previous_reports:
        previous_sender = report["sender_email"]
        previous_domain = previous_sender.split("@")[1]
        previous_time = datetime.fromisoformat(report["reported_at"])

        if previous_sender == current_sender or previous_domain == current_domain:
            time_difference = current_time - previous_time

            if timedelta(0) <= time_difference <= timedelta(hours=24):
                match_count += 1

    if match_count >= 3:
        return True

    return False

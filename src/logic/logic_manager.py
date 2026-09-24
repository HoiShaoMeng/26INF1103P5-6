#fail safe check: True if ai_manager cant get a real AI response and returned the AI_UNAVAILABLE placeholder instead. 
#classify_severity() must run this first so a failed AI call never gets mistaken for a "safe" email.
def is_ai_unavailable(ai_output):

    if not isinstance(ai_output, dict):
        return False

    return ai_output.get("classification") == "AI_UNAVAILABLE"

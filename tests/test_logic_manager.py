#ONLY FOR TESTING!
#hard coded test cases for logic_manager.py, every ai_output below is a fake dict, no AI API calls.
#to run, enter this in terminal: python3 tests/test_logic_manager.py

import os
import sys

#adds the src/logic folder to the path so we can import logic_manager.py for testing.
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "src", "logic")
)

from logic_manager import is_ai_unavailable  # type: ignore #pulls in the ACTUAL function from logic_manager.py for testing. #the "type: ignore" is to silence a false positive IDE warning
                                                
#test case: a properly formed AI_UNAVAILABLE placeholder should be detected as unavailable
def test_is_ai_unavailable_true_when_classification_matches():
    fake_ai_output = {
        "classification": "AI_UNAVAILABLE",
        "threat_level": 0,
        "tactics_detected": [],
        "suspicious_urls": [],
        "suspicious_attachments": [],
        "sender_domain_mismatch": False,
    }
    assert is_ai_unavailable(fake_ai_output) is True #call the real function, fail if it doesn't return True

#test case: a normal successful AI response should NOT be flagged as unavailable
def test_is_ai_unavailable_false_for_normal_classification():
    fake_ai_output = {
        "classification": "phishing",
        "threat_level": 92,
        "tactics_detected": ["executive_impersonation"],
        "suspicious_urls": ["http://bad-domain.example/login"],
        "suspicious_attachments": [],
        "sender_domain_mismatch": True,
    }
    assert is_ai_unavailable(fake_ai_output) is False

#test case: if classification key is missing entirely, should default safely to False, not crash
def test_is_ai_unavailable_false_when_classification_missing():
    fake_ai_output = {"threat_level": 10, "tactics_detected": []}
    assert is_ai_unavailable(fake_ai_output) is False

#test case: garbage input types (None, strings, a list) should default safely to False
def test_is_ai_unavailable_false_for_malformed_input():
    #Must not crash on bad input, classify_severity() relies on this as a safe first check.
    assert is_ai_unavailable(None) is False
    assert is_ai_unavailable("AI_UNAVAILABLE") is False
    assert is_ai_unavailable([]) is False

#runs every test above in sequence and prints a pass/fail summary
def _run_all_tests():
    tests = [
        test_is_ai_unavailable_true_when_classification_matches,
        test_is_ai_unavailable_false_for_normal_classification,
        test_is_ai_unavailable_false_when_classification_missing,
        test_is_ai_unavailable_false_for_malformed_input,
    ]
    for test in tests: #go through the list one at a time (4 times) and run each test function, if it fails the assert will throw an exception and stop the test.
        test() #calls whatever test function is currently in the loop, e.g. test_is_ai_unavailable_true_when_classification_matches()
        print(f"PASSED: {test.__name__}") #print the name of the test function if it did not crash
    print(f"{len(tests)} test(s) passed.") #print the total count of tests after the loop finishes.

#runs only when the file is executed directly (python3 tests/test_logic_manager.py)
if __name__ == "__main__":
    _run_all_tests()

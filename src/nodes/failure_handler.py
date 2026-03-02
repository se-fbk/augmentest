import os

from src.llm.base import LLMClient
from src.run_augmentestagentic import GlobalState


# this function is called because AugmenTest failed to improve the original test case
# it saves the original test case and report that attempts to improve it have failed.
def handle_failure(state: GlobalState, model: LLMClient) -> dict:
    error_message = "// AugmenTest failed to improve this test case. Please review it carefully as it may not be correct."
    test_code = (error_message +
                 os.linesep +
                 state.current_test.get("test_code"))
    # get the current test and update it
    current_test = state.current_test
    current_test["formatted_test_code"] = test_code
    return {
         "current_test": current_test,
    }

import time

from common.string_tables import string_tables
from preprocessing.java_parser import JavaClassParser
from src.run_augmentestagentic import GlobalState
from src.utils.tools import is_syntactically_correct, prepare_temp_test_and_check_compilation
from utils.tools import compile_test_case, compile_and_run_test_case


def validate(state: GlobalState) -> dict:
    compilation_attempt = state.compilation_count + 1
    print(f"   --- 🔍 VALIDATOR ---")
    return_state = None

    # get the current test and update it
    current_test = state.current_test
    test_code = current_test.get("test_code")

    test_num = current_test["ID"]
    temp_test_suite = current_test.get("class_name") + '_' + str(test_num) + string_tables.AUGMENTEST_SIGNATURE
    import re
    formatted_test = re.sub(r"\b" + re.escape(state.current_test.get("class_name")) + r"\b", temp_test_suite, test_code)

    if state.run_augmentest_evaluation:
        ##########################################################
        ### Additional steps for Augmentest Evaluation : START ###
        ### COMPILE and RUN Original (EvoSuite) unit test      ###
        ##########################################################

        # get the current test and update it
        current_test = state.current_test
        original_test_code = current_test.get("original_test_code")

        temp_original_test_suite = current_test.get("class_name") + '_' + str(
            test_num) + string_tables.EVOSUITE_UNIT_SIGNATURE
        import re
        formatted_original_test = re.sub(r"\b" + re.escape(state.current_test.get("class_name")) + r"\b",
                                         temp_original_test_suite,
                                         original_test_code)

        # COMPILE and RUN Original (EvoSuite) unit test
        is_compiled_original, compilation_log_original, is_run_original, run_log_original = compile_and_run_test_case(
            formatted_original_test,
            state.current_test.get("test_path"),
            temp_original_test_suite,
            # state.current_test.get("method_name"),
            # state.current_test.get("project_name"),
            state.current_test.get("package_name"),
            state.project_root)

        if is_compiled_original:
            print("      ✅ Original Test compiled successfully.")
            if is_run_original:
                print("      ✅ Original Test run successfully.")
            else:
                print("      ❌ Original Test Run Failed.")
                print(compilation_log_original)
        else:
            print("      ❌ Original Test Compilation Failed.")
            print(compilation_log_original)

        # COMPILE and RUN AugmenTest unit test
        is_compiled_augmentest, compilation_log_augmentest, is_run_augmentest, run_log_augmentest = compile_and_run_test_case(
            formatted_test,
            state.current_test.get("test_path"),
            temp_test_suite,
            # state.current_test.get("method_name"),
            # state.current_test.get("project_name"),
            state.current_test.get("package_name"),
            state.project_root)

        if is_compiled_augmentest:
            print("      ✅ Augmentest Test compiled successfully.")
            if is_run_augmentest:
                print("      ✅ Augmentest Test run successfully.")
            else:
                print("      ❌ Augmentest Test Run Failed.")
                print(compilation_log_augmentest)
        else:
            print("      ❌ Augmentest Test Compilation Failed.")
            print(compilation_log_augmentest)
        ########################################################
        ### Additional steps for Augmentest Evaluation : END ###
        ########################################################
    else:
        # COMPILE AugmenTest unit test
        is_compiled_augmentest, compilation_log_augmentest = compile_test_case(
            formatted_test,
            state.current_test.get("test_path"),
            temp_test_suite,
            # state.current_test.get("method_name"),
            # state.current_test.get("project_name"),
            state.current_test.get("package_name"),
            state.project_root)

    # print results and update state
    if is_compiled_augmentest:
        print("      ✅ Test compiled successfully.")
        current_test["test_code"] = formatted_test
        current_test["class_name"] = temp_test_suite
        return_state = {"error_logs": None, "current_test": current_test, "compilation_attempt": compilation_attempt}
    else:
        print("      ❌ Compilation Failed.")
        print()
        return_state = {"error_logs": compilation_log_augmentest, "compilation_attempt": compilation_attempt}

    return return_state
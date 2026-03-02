# ---------------------------------------------------------
# Script: Test Oracle Generator
# Developer: Shaker Mahmud Khandaker
# Project: AugmenTest
# Last Updated: December 16, 2025
# Purpose: Main script for generating oracles
#          using multiple LLM-based
#          assertion generation approaches.
# ---------------------------------------------------------

import os.path
import time

from src.config.config import *
from src.preprocessing.preprocessor import build_context_for_test_case

from src.utils.tools import *
import sys
from colorama import Fore, Style
from src.common.variants import Variants
from src.llm.prompts import generate_messages


def generate_oracles(project_path, target_class, target_method,
                     llm_model, generation_strategy, include_comments):
    """
    Generate test oracles using specified LLM strategy

    Args:
        project_path: Root project directory
        target_class: Class to analyze
        target_method: Method to generate oracles for
        llm_model: LLM model to use
        generation_strategy: Oracle generation variant
        include_comments: Whether to consider developer comments

    Returns:
        Result of oracle generation
    """

    llm_response = ""
    assertions = ""

    # Map strategy name to Variants enum
    strategy_map = {
        Variants.SIMPLE_PROMPT.name: Variants.SIMPLE_PROMPT,
        Variants.EXTENDED_PROMPT.name: Variants.EXTENDED_PROMPT,
        Variants.RAG.name: Variants.RAG,
        Variants.SIMPLE_PROMPT_WITH_RAG.name: Variants.SIMPLE_PROMPT_WITH_RAG
    }

    selected_strategy = strategy_map.get(generation_strategy, Variants.SIMPLE_PROMPT)

    # Generate test cases
    context = build_context_for_test_case(project_path, target_class, target_method)

    steps, rounds = 0, 0

    # Get the current time in milliseconds
    start_time = time.perf_counter()
    end_time = time.perf_counter()

    result = {
        "attempts": 0,  # int
        "assertion_generated": False,  # bool
        "assertion_generation_time": 0.0,  # float (not int!)
        "oracle": None,  # str | None
        "prompts_and_responses": [],  # list (not None)
        "variant": "",  # string (not None)
        "full_test_code": ""  # contains the full test code returned by the model
    }

    prompts_and_responses = []

    if not include_comments:
        context["focal_method_details"] = remove_key_value_pair_from_json(context.get("focal_method_details"),
                                                                          "developer_comments")

        # print("AFTER REMOVING DEV COMMENTS:")
        # print(context["focal_method_details"])

    try:
        while rounds < max_attempts:
            # 1. Prompt LLM
            steps += 1
            rounds += 1

            if selected_strategy == Variants.SIMPLE_PROMPT:
                prompt_template = SP_TEMPLATE
                messages = generate_messages(prompt_template, context)
            elif selected_strategy == Variants.EXTENDED_PROMPT:
                all_method = json.loads(context["class_method_details"])

                if len(all_method) > 0:
                    prompt_template = EP_TEMPLATE
                else:
                    prompt_template = SP_TEMPLATE

                messages = generate_messages(prompt_template, context)
            elif selected_strategy == Variants.RAG:
                prompt_template = RAG_GEN_TEMPLATE
                messages = generate_messages(prompt_template, context)
            elif selected_strategy == Variants.SIMPLE_PROMPT_WITH_RAG:
                prompt_template = RAG_SP_TEMPLATE
                messages = generate_messages(prompt_template, context)
            else:
                return "Invalid variant"

            # print("Prompt: " + Fore.YELLOW + messages, Style.RESET_ALL)

            # print("Attempt: " + Fore.YELLOW + str(rounds), Style.RESET_ALL)

            # if selected_strategy == Variants.RAG or selected_strategy == Variants.SIMPLE_PROMPT_WITH_RAG:
            #     # OpenAI RAG
            #     project_id = os.path.basename(os.path.dirname(os.path.dirname(project_path)))
            #     # print("PROJECT_ID : " + project_id)
            #     llm_raw_response, llm_extracted_response = prompt_OpenAI_RAG(messages, project_id)
            #
            #     # assertions = llm_extracted_response
            #     # assertions = extract_code_block_statements(llm_extracted_response)
            # else:
            #     llm_raw_response = llm_model.query(messages)

            llm_response = llm_model.query(messages)

            assertions = extract_complex_assertion(llm_response)

            # If a non-empty assertion was found, update 'assertion_generated' to TRUE
            if assertions:
                assertions = semicolonFormatter(assertions)
            else:
                assertions = extract_simple_assertion(llm_response)
                if assertions:
                    assertions = semicolonFormatter(assertions)

            prompts_and_responses.append({"prompt": messages, "response": str(llm_response), "attempt": str(rounds),
                                          "variant": selected_strategy.name})

            steps += 1

            if assertions:
                print("Assertion generation: " + Fore.GREEN + "SUCCESS", Style.RESET_ALL)
                # print("LLM Response Assertion: " + Fore.GREEN + assertions, Style.RESET_ALL)
                # print()

                end_time = time.perf_counter()

                print("Assertion: " + Fore.GREEN + assertions, Style.RESET_ALL)

                result["assertion_generated"] = True
                result["oracle"] = assertions
            else:
                print("Assertion generation: " + Fore.RED + "FAILED", Style.RESET_ALL)
                end_time = time.perf_counter()

        result["attempts"] = rounds

    except Exception as e:
        print(Fore.RED + str(e), Style.RESET_ALL)
        end_time = time.perf_counter()

    assertion_generation_time = (end_time - start_time) * 1000

    result["assertion_generation_time"] = assertion_generation_time
    result["prompts_and_responses"] = prompts_and_responses
    result["variant"] = selected_strategy.name

    full_code = context["test_case_with_placeholder"].replace(
        string_tables.ASSERTION_PLACEHOLDER,
        assertions or "// FAILED"
    )
    result["full_test_code"] = full_code
    result["original_test_code"] = context["evosuite_test_case"]

    return result
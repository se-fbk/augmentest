# ---------------------------------------------------------
# Script: Agentic AugmenTest Automation Pipeline
# Developer: Fitsum Kifetew, Shaker Mahmud Khandaker
# Project: Agentic-AugmenTest
# Purpose: End-to-end test processing from project directory to oracle generation and readability improvement
# ---------------------------------------------------------

import asyncio
import shutil
import sys
import json
import time
import logging
import traceback
from pathlib import Path
from typing import Any

import requests
import re
import os
from typing import Literal
from typing import Optional, List, Dict, Annotated
from gpt4all import GPT4All
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from colorama import Fore, Style
from langgraph.constants import END
from langgraph.graph import StateGraph
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver

from llm.gemini_client import GeminiModelClient
from src.common.resource_manager import ResourceManager
from src.preprocessing.preprocessor import build_context_for_test_case

augmentest_root = os.path.dirname(os.path.realpath(__file__))
# local_mcp_servers_dir = os.path.join(augmentest_root, "mcp_servers/")

# add project root to PYTHONPATH
sys.path.append(os.path.join (augmentest_root, ".."))

# import local modules
# NOTE this should be after updating PYTHONPATH (above),
# otherwise python will not find the modules
from src.common.string_tables import string_tables
from src.common.variants import Variants
from src.config.config import *
from src.oracle_generation.oracle_generator import generate_oracles
from src.llm.base import LLMClient
from src.llm.mock import MockModelWrapper
from src.llm.llamacpp_client import LLamaCPPModelClient
from src.llm.gpt4all_client import GPT4AllModelClient
from src.llm.gemini_client import GeminiModelClient
from src.preprocessing.preprocessor import execute_processing

# TODO this is currently hard-coded for simplicity, should be passed as argument to the script
# local_project_root = os.path.join(augmentest_root, "../suts/simple_calculator/")
# local_sut_classpath = os.path.join(local_project_root, "target/classes")

# choose whichever implementation you want:
# aug_model: LLMClient = MockModelWrapper()
aug_model: LLMClient = LLamaCPPModelClient()
oracle_model: LLMClient = LLamaCPPModelClient()
# aug_model: LLMClient = GPT4AllModelClient()
# aug_model: LLMClient = GeminiModelClient()


# ==========================================
# 2. STATE DEFINITIONS
# ==========================================

# This function tells LangGraph: "When a new value comes in, ignore the old one."
def replace_fn(old_value, new_value):
    return new_value

class GlobalState(BaseModel):
    # --- INPUTS ---
    project_root: str
    test_output_dir: str
    programming_language: str

    # --- EVALUATION ---
    # Flag to enable/disable the extra evaluation steps
    run_augmentest_evaluation: bool = True
    # Metrics for the CURRENT test being processed.
    # Nodes (e.g., generator, validator) will populate keys here (e.g., 'eo_compiled_original', 'total_time')
    # (to be saved to CSV)
    current_eval_metrics: Dict[str, Any] = Field(default_factory=dict)

    # --- QUEUE & STATUS ---
    list_of_tests: List[Dict[str, str]] = Field(default_factory=list)
    preprocessing_done: bool

    # --- WORKFLOW DATA ---
    completed_tests: List[str] = Field(default_factory=list)

    # --- CURRENT TASK CONTEXT ---
    current_test: Dict[str, str] = {}

    # --- FEEDBACK & COUNTERS ---
    error_logs: Annotated[Optional[str], replace_fn] = None
    generation_count: int = 0
    compilation_count: int = 0

    # --- CONFIG ---
    max_generations: int = 3
    max_compilations: int = 3


# ==========================================
# 3. OUTER LOOP NODES (Orchestration)
# ==========================================

# AugmenTest preprocessor that reads the project root from disk, parses the existing code and test cases.
# The results of the preprocessing are stored on disk in a json database
# Part of this databases is kept in memory in the GlobalState and used by the different nodes of the architecture.
def preprocessor_node(state: GlobalState) -> dict:
    # pre-process the project SUT --> json_db on disk
    # test cases are assumed to be in the project!

    # this should populate the json_db on disk, whose file path is in config.ini
    execute_processing(state.project_root, state.programming_language)

    manager = ResourceManager(state.project_root + db_json_file)

    project_name = os.path.basename(os.path.normpath(state.project_root))
    list_of_classes = manager.get_classes_with_contains_test(project_name)

    list_of_tests = []
    # Loop through the results
    test_id = 0
    for cls in list_of_classes:
        class_name = cls.get("class_name")
        # package_name = manager.get_package_by_project_and_class(project_name, class_name)
        methods = cls.get("methods")

        # Loop through the results
        for test in methods:
            project_name = test.get("project_name")
            method_name = test.get("method_name")
            context = build_context_for_test_case(state.project_root, class_name, method_name)
            test_code = context.get("evosuite_test_case")
            package_name = context.get("package")
            test_method_details = context.get("focal_method_details")
            test_path = context.get("test_class_path")
            list_of_tests.append({
                "ID": str(test_id),
                "project_name": project_name,
                "project_dir": state.project_root,
                "class_name": class_name,
                "package_name": package_name,
                "method_name": method_name,
                "test_code": test_code,
                "test_path": test_path,
                "test_method_details": test_method_details,
            })
            test_id += 1

    return {
        "list_of_tests": list_of_tests,
        "preprocessing_done": True
    }

def scheduler_node(state: GlobalState) -> dict:
    """
    Pick the next test from the queue.
    If queue empty, we are done.
    If not, setup the state for the Inner Loop.
    """
    # Check if we have processed everything
    # Note: Ideally we'd remove items from the list.
    # Here we check length of completed vs total, or pop from list.

    # Logic: We define 'remaining' as items not yet in completed list count
    # But simpler for LangGraph: We pop from 'list_of_tests' if we treat it as a queue
    # However, 'state' could be immutable in some versions, so we return modified lists.

    # iterate over the test cases and update the GlobalState with the relevant information
    if not state.list_of_tests:
        return {"current_test" : {}}

    current_test = state.list_of_tests[0]
    if len(state.list_of_tests) > 1:
        remaining_tests = state.list_of_tests[1:]
    else:
        remaining_tests = []

    current_test_id = current_test.get("ID")
    print(f"=== 🔄 SCHEDULER: Next -> TestID :{current_test_id} ===")

    # RESET all inner loop counters and buffers
    return {
        "list_of_tests": remaining_tests,  # Update queue
        "current_test": current_test,
        "current_requirements": None,
        "current_assertions": None,
        "error_logs": None,
        "critique_feedback": None,
        "refine_count": 0,
        "generation_count": 0,
        "compilation_count": 0
    }


def saver_node(state: GlobalState) -> dict:
    """
    A simple node that saves test suites to disk.
    NOTE: This is a temporary implementation
    """
    from src.utils.tools import change_class_name, export_method_test_case

    test_suite_source_code = state.current_test.get("test_code")
    # state.current_test.get("test_path")
    class_name = state.current_test.get("class_name")
    test_num = state.current_test.get("ID")
    # state.current_test.get("method_name")
    # state.current_test.get("project_name")
    package_name = state.current_test.get("package_name")


    # temp_test_suite = class_name + '_' + str(test_num) + string_tables.EVOORACLE_SIGNATURE
    # temp_test_suite_source_code = change_class_name(test_suite_source_code, class_name, temp_test_suite)

    # export temp test case
    package_path = Path(os.path.join (state.test_output_dir, package_name.replace('.', os.sep)))
    package_path.mkdir(parents=True, exist_ok=True)
    # temp_out_dir = os.path.dirname(package_path)
    temp_test_file_name = export_method_test_case(package_path.as_posix(), class_name, test_suite_source_code)
    print(f"=== 💾 SAVER: Saved {temp_test_file_name} ===")

    # Add the filename to the completed list (instead of full code)
    new_completed = state.completed_tests + [temp_test_file_name]
    return {"completed_tests": new_completed}


# ==========================================
# 4. INNER LOOP NODES (AugmenTest Agentic Cycle)
# ==========================================

# This is the assertion generation node alla AugmenTest
def oracle_generator_node(state: GlobalState) -> dict:
    gen_attempt = state.generation_count + 1
    print(f"   --- 🤖 GENERATOR (Attempt {gen_attempt}) ---")

    context = build_context_for_test_case(state.project_root,
    state.current_test.get("class_name"),
    state.current_test.get("method_name"))

    oracle_generation_result = generate_oracles(state.project_root,
    state.current_test.get("class_name"),
    state.current_test.get("method_name"),
    oracle_model,
    Variants.SIMPLE_PROMPT,
    True)

    # assertions = oracle_generation_result["oracle"]
    # full_code = context["test_case_with_placeholder"].replace(
    #     string_tables.ASSERTION_PLACEHOLDER,
    #     assertions or "// FAILED"
    # )

    full_code = oracle_generation_result["full_test_code"]
    # get the current test and update it
    current_test = state.current_test
    current_test["test_code"] = full_code
    current_test["original_test_code"] = oracle_generation_result["original_test_code"]

    return {
        # "current_assertions": assertions,
        # "current_test_code": full_code,
        "current_test": current_test,
        "current_context": context,
        # "current_requirements": context.get("focal_method_details"),
        "generation_count": gen_attempt,
        "critique_feedback": None,
        "error_logs": None
    }


# This is already there in AugmenTest ..
def validator_node(state: GlobalState) -> dict:
    from src.nodes.validator import validate
    return validate(state)

# AugmenTest failed to improve the test, so save it as is with a warning to inform the user
def failure_handler_node(state: GlobalState) -> dict:
    from src.nodes.failure_handler import handle_failure
    return handle_failure(state, aug_model)

# ==========================================
# 5. ROUTING LOGIC
# ==========================================

def route_scheduler(state: GlobalState) -> Literal["preprocessor", "generator", "end"]:
    """
    Determines if there are tasks left.
    """
    # If we just started (no prefixes generated yet), run preprocessor
    if not state.preprocessing_done:
        return "preprocessor"

    # If scheduler returned empty for current_test, queue is empty
    if (len(state.current_test)) == 0:
        return "end"

    # Otherwise, start the inner loop
    return "generator"


# ==========================================
# 6. BUILD GRAPH
# ==========================================

workflow = StateGraph(GlobalState)

# Add Nodes
workflow.add_node("preprocessor", preprocessor_node)
workflow.add_node("scheduler", scheduler_node)
workflow.add_node("generator", oracle_generator_node)
workflow.add_node("validator", validator_node)
workflow.add_node("saver", saver_node)
workflow.add_node("failure_handler", failure_handler_node)


# entry point
workflow.set_entry_point("scheduler")

# Edge: Scheduler -> (Preprocessor OR Generator OR End)
workflow.add_conditional_edges(
    "scheduler",
    route_scheduler,
    {
        "preprocessor": "preprocessor",
        "generator": "generator",
        "end": END
    }
)

# Edge: Preprocessor -> Scheduler (to pick the first task)
workflow.add_edge("preprocessor", "scheduler")

# Edge: OracleGenerator -> Validator
workflow.add_edge("generator", "validator")

# conditional edge: Validator -> Saver OR CompilationFixer OR FailureHandler
def route_validator(state: GlobalState) -> Literal["saver", "generator", "failure_handler"]:
    failed_validation = state.error_logs is not None and len(state.error_logs) > 0

    if not failed_validation:
        return "saver"  # Success

    if state.compilation_count < state.max_compilations & state.generation_count < state.max_generations:
        return "generator"

    return "failure_handler"

# conditional edge: Validator -> Saver OR CompilationFixer
workflow.add_conditional_edges(
    "validator",
    route_validator,
    {
        "saver": "saver",
        "generator": "generator",
        "failure_handler": "failure_handler"
    }
)

# Edge: FailureHandler -> Saver
workflow.add_edge("failure_handler", "saver")

# Edge: Saver -> Scheduler (Loop back to pick next task)
workflow.add_edge("saver", "scheduler")

# The checkpointer provides the "storage" that sync/async modes operate on
checkpointer = MemorySaver()
app = workflow.compile(checkpointer)

# ==========================================
# 7. EXECUTION
# ==========================================


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Handle user input.")

    # Positional argument (required)
    parser.add_argument("project_root", type=str, help="The absolute path to the root of the project under test.")

    # Optional argument test_output_dir
    parser.add_argument("--test_output_dir", type=str, default=None, help="The absolute path to the directory to store the test output. "
                                                                          "Contents will be deleted if it exists, otherwise it will be created. "
                                                                          "Defaults to <project_root>/" + string_tables.DEFAULT_TEST_OUTPUT_FOLDER + ".")

    # Optional argument max_refines
    parser.add_argument("--max_refines", type=int, default=3, help="Maximum number of attempts to refine a test case.")

    # Optional argument max_generations
    parser.add_argument("--max_generations", type=int, default=3, help="Maximum number of attempts to generate an oracle.")

    # Optional argument max_generations
    parser.add_argument("--max_compilations", type=int, default=3, help="Maximum number of attempts to compile a test case.")

    # Optional argument dump_graph
    parser.add_argument("--dump_graph", type=bool, default=False, help="Save the graph to disk, file augmentestagent.png")

    args = parser.parse_args()


    print("🚀 Starting Workflow with Class Config...")

    # ---------------------------------------------------------
    # Add 'config' with 'recursion_limit'
    # ---------------------------------------------------------
    # Calculation estimate:
    # (Preprocessor + Generator (2) + Critic + Refiner (3) + Validator + Readability + Saver + Scheduler) ≈ 11 steps per test (MAX).
    # If you have 10 tests, you should need about 110 steps, so 150 is a safe value.

    agent_config = {
        "recursion_limit": 5000,
        "max_concurrency": 1, # Forces sequential execution
        "configurable": {
            "thread_id": "unique-session-id-123",  # This is required to ensure proper synchronization
        },
        # "durability": "sync" # ensure writes are fully synchronized before next node
    }

    # prepare some global vars
    if args.test_output_dir is None:
        test_output_dir = os.path.join(args.project_root, string_tables.DEFAULT_TEST_OUTPUT_FOLDER)
    else:
        test_output_dir = args.test_output_dir

    # TODO this is temporary, actual strategy to be decided.
    # make sure that the output folder is empty, deleting any existing tests from previous runs
    if os.path.exists(test_output_dir):
        shutil.rmtree(test_output_dir, ignore_errors=True)

    inputs = {
        "project_root": args.project_root,
        "test_output_dir": test_output_dir,
        "programming_language": "java",
        "preprocessing_done": False,
        "max_refines": args.max_refines,
        "max_generations": args.max_generations,
        "max_compilations": args.max_compilations
    }

    try:
        ### visualize graph, uncomment to generate a figure of the graph
        if args.dump_graph:
            from IPython.display import Image, display
            display(Image(app.get_graph().draw_mermaid_png(output_file_path="augmentestagent.png")))
            with open("augmentestagent.mrmd", "w") as file:
                file.write(app.get_graph().draw_mermaid())

        result = await app.ainvoke(inputs, config=agent_config, durability="sync")

        print("\n" + "=" * 50)
        if "completed_tests" in result:
            print(f"🎉 GENERATED {len(result['completed_tests'])} TESTS")
        else:
            print("No test case produced. Either non tests were found for the given project or the pipeline failed to properly process them.")
        print("=" * 50)

    except Exception as e:
        print(f"❌ Execution failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

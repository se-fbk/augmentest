# ---------------------------------------------------------
# Script: Test Oracle Generator
# Developer: Shaker Mahmud Khandaker
# Project: AugmenTest
# Last Updated: March 18, 2025
# Purpose: Main script for processing test cases and 
#          generating oracles using multiple LLM-based
#          assertion generation approaches.
# ---------------------------------------------------------

import uuid
import sys
from tools import *
from test_processor import prepare_test_cases
from colorama import Fore, Style, init
from variants import Variants

def generate_oracles(test_id, project_path, target_class, target_method, 
                    model_name, generation_strategy, include_comments, 
                    is_fix_run=False, assertion_fix=""):
    """
    Generate test oracles using specified LLM strategy
    
    Args:
        test_id: Unique test identifier
        project_path: Root project directory
        target_class: Class to analyze
        target_method: Method to generate oracles for
        model_name: LLM model to use
        generation_strategy: Oracle generation variant
        include_comments: Whether to consider developer comments
        is_fix_run: Flag for correction runs (default False)
        assertion_fix: Assertion to fix (default empty)
    
    Returns:
        Result of test case preparation
    """
    # Create unique execution ID
    unique_id = str(uuid.uuid4()).replace('-', '')[:12]
    execution_id = f"_{unique_id}"
    
    # Map strategy name to Variants enum
    strategy_map = {
        Variants.SIMPLE_PROMPT.name: Variants.SIMPLE_PROMPT,
        Variants.EXTENDED_PROMPT.name: Variants.EXTENDED_PROMPT,
        Variants.RAG.name: Variants.RAG,
        Variants.SIMPLE_PROMPT_WITH_RAG.name: Variants.SIMPLE_PROMPT_WITH_RAG,
        Variants.TOGA_DEFAULT.name: Variants.TOGA_DEFAULT,
        Variants.TOGA_UNFILTERED.name: Variants.TOGA_UNFILTERED
    }
    
    selected_strategy = strategy_map.get(generation_strategy, Variants.SIMPLE_PROMPT)
    
    # Generate test cases
    return prepare_test_cases(
        test_id, execution_id, project_path, target_class, 
        target_method, model_name, selected_strategy, 
        include_comments, is_fix_run, assertion_fix
    )

if __name__ == '__main__':
    # Verify command line arguments
    if len(sys.argv) > 7:
        # Parse arguments
        test_identifier = sys.argv[1]
        project_path = sys.argv[2]
        class_to_test = sys.argv[3]
        method_to_test = sys.argv[4]
        llm_model = sys.argv[5]
        variant_type = sys.argv[6]
        parse_comments = sys.argv[7].lower() == "true"
        
        # Execute oracle generation
        generate_oracles(
            test_identifier, project_path, class_to_test,
            method_to_test, llm_model, variant_type,
            parse_comments
        )
    else:
        error_msg = "Execution failed - Required arguments: "
        error_msg += "test_id project_dir class_name method_name "
        error_msg += "llm_name variant consider_dev_comments"
        print(Fore.RED + error_msg, Style.RESET_ALL)
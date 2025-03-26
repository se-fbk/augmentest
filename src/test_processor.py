"""
This class will process all the test files: extract test cases, replace assertions, prepares contexts.
"""
import time
from resource_manager import ResourceManager
from string_tables import string_tables
from tools import *
from llm_prompter import generate_oracle_with_LLM
from utilities import ProjectUtilities
from colorama import Fore, Style, init
import csv
import os
from datetime import datetime
from oracle_types import Oracles

init()

def prepare_test_cases_entries(project_dir):
    """
    - Iterates through tests
    - Prepares csv file with all entries
    :param project_dir:
    :return:    
    """
    # First ensure the directory exists
    os.makedirs(os.path.dirname(augmentest_csv_input), exist_ok=True)

    if not os.path.exists(augmentest_csv_input):
        # If it doesn't exist, create the file with a header row
        with open(augmentest_csv_input, mode='w', newline='') as csv_file:
            fieldnames = ["ID"] + ["project_dir", "class_name", "method_name"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

    # Read the existing CSV file to find the last ID used
    last_id = 0
    with open(augmentest_csv_input, mode='r') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            last_id = int(row["ID"])

    # Increment the last ID to generate a new ID
    new_id = last_id + 1

    with open(augmentest_csv_input, mode='a', newline='') as csv_file:
        fieldnames = ["ID"] + ["project_dir", "class_name", "method_name"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        # Write the header row
        # writer.writeheader()
    
        project_name = os.path.basename(os.path.normpath(project_dir))
        
        print("Project_name: ", Fore.GREEN + project_name, Style.RESET_ALL)
        
        # get the classes that contains tests.
        manager = ResourceManager(project_dir + db_json_file)
        class_results = manager.get_classes_with_contains_test(project_name)

        # Loop through the results
        for row in class_results:
            class_name = row.get("class_name")
            methods = row.get("methods")

            # Loop through the results
            for row in methods:
                project_name  = row.get("project_name")
                method_name = row.get("method_name")
                writer.writerow({
                    "ID": new_id,
                    "project_dir": project_dir,
                    "class_name": class_name,
                    "method_name": method_name
                })
                new_id = new_id + 1
            
        print("CSV generation: ", Fore.GREEN + "SUCCESS", Style.RESET_ALL)

def prepare_test_cases(test_id, execution_id, project_dir, class_name, method_name, llm_name, variant, consider_dev_comments, fix_run, fix_assertion):
    """
    - Get test details
    - Replaces Assertions
    - Prepares contexts for each tests
    :param project_dir:
    :param class_name:
    :param method_name:
    :return:    
    """
    
    project_name = os.path.basename(os.path.normpath(project_dir))
    
    print("Project Name: ", Fore.GREEN + project_name, Style.RESET_ALL)
    print("Test Class Name: ", Fore.GREEN + class_name, Style.RESET_ALL)
    print("Test Method Name: ", Fore.GREEN + method_name, Style.RESET_ALL)

    # get the classes that contains tests.
    manager = ResourceManager(project_dir + db_json_file)
    class_details = manager.get_class_details_from_projectname_classname(project_name, class_name)

    signature = class_details.get("signature")
    super_class = class_details.get("super_class")
    package = class_details.get("package")
    stripped_package = class_details.get("package").split(' ')[1].strip(';')
    imports = class_details.get("imports")
    fields = class_details.get("fields")
    has_constructor = class_details.get("has_constructor")
    contains_test = class_details.get("contains_test")
    dependencies = class_details.get("dependencies")
    methods = class_details.get("methods")
    argument_list = class_details.get("argument_list")
    interfaces = class_details.get("interfaces")
    test_class_name = class_details.get("class_name")
    test_class_path = class_details.get("class_path")
    
    # Define a list to store replaced assertions for each method
    # replaced_assertions_per_method = {}

    test_method_details = manager.get_details_by_project_class_and_method(project_name, test_class_name, method_name, False)
    focal_methods = test_method_details["focal_methods"]
    source_code = test_method_details["source_code"]
    
    source_code = remove_all_assertions_but_last(source_code)
    source_code = remove_empty_lines(source_code)

    # prepare the test case
    evosuite_test_case = package + string_tables.NL +  imports + string_tables.NL + signature + string_tables.NL + string_tables.LEFT_CURLY_BRACE + string_tables.NL + source_code + string_tables.NL + string_tables.RIGHT_CURLY_BRACE

    # Regular expression pattern to match assertions
    source_code, replaced_assertions = replace_assertions(source_code)

    # prepare the test case
    test_case_with_placeholder = package + string_tables.NL +  imports + string_tables.NL + signature + string_tables.NL + string_tables.LEFT_CURLY_BRACE + string_tables.NL + source_code + string_tables.NL + string_tables.RIGHT_CURLY_BRACE

    test_method_details["source_code_with_placeholder"] = source_code

    # focal_methods = json.loads(focal_method_name)
    
    # overriding the CUT from DB Json to Test Filename
    class_under_test = get_CUT_from_test_class_name(test_class_name)
    class_under_test_details = manager.get_class_details_from_projectname_classname(project_name, class_under_test)
    
    class_under_test_fields = class_under_test_details.get("fields")
    class_under_test_fields = remove_empty_lines(class_under_test_fields)

    cut_methods = class_under_test_details.get("methods")
    # prepare the context
    
    MUT_list = set()  # Create an empty set to store unique MUT
    
    for focal_method in focal_methods:
        mut = get_MUT_from_string(focal_method)
        MUT_list.add(mut)

    MUT_list = list(MUT_list)
    
    method_details_list = []

    for MUT in MUT_list:
        method_details = manager.get_details_by_project_class_and_method(project_name, class_under_test, MUT, True)
        if method_details:
            method_details_list.append(method_details)
    
    # Pretty print JSON (but after the loop, not before)
    # print("MUT : " + json.dumps(method_details_list, indent=2))
    
    encoding = tiktoken.encoding_for_model("gpt-4o")
    
    class_method_comments_list = []
    for class_method in cut_methods:
        cut_method_name = class_method.get("method_name")
        cut_comment = class_method.get("dev_comments")
        cut_return_type = class_method.get("return_type")
        details = {
            "method_name": cut_method_name,
            "developer_comments": cut_comment,
            "return_type": cut_return_type,
        }

        # Check if the parameters match any in method_details_list
        exists = False
        for foc_method in method_details_list:
            if foc_method.get("parameters") == class_method.get("parameters"):
                exists = True
                break
        
        # Append details only if it doesn't exist
        if not exists:
            # Encode the string to get the list of tokens
            tokens = encoding.encode(str(class_method_comments_list))

            # Get the number of tokens
            token_count = len(tokens)
            # print(f"Token count: {token_count}")
            if token_count < 20000:
                class_method_comments_list.append(details)
            else:
                break

    # Pretty print JSON
    # print("class_method_comments_list : " + json.dumps(class_method_comments_list, indent=2))
    
    # print("CUT: ", Fore.GREEN + class_under_test, Style.RESET_ALL)
    # print("MUT: \n", Fore.YELLOW + "\n".join(MUT_list), Style.RESET_ALL)
    # print()
    
    # method_under_test_details = manager.get_details_by_project_class_and_method(project_name, class_under_test, method_under_test, False)

    # # print(method_under_test_details)
    # if method_under_test_details:
    #     dev_comments = method_under_test_details.get("dev_comments")
    # else:
    #     dev_comments = None

    method_details_list = json.dumps(method_details_list, indent=2)
    class_method_list = json.dumps(class_method_comments_list, indent=2)

    context = {"project_name": project_name, "class_name": class_under_test, "fields":class_under_test_fields, "test_class_path":test_class_path, "test_class_name": test_class_name, 
           "test_method_name":method_name, "focal_method_details": method_details_list, "class_method_details": class_method_list, "test_method_code": source_code, 
            "assertion_placeholder": string_tables.ASSERTION_PLACEHOLDER, "test_case_with_placeholder":test_case_with_placeholder, 
            "package":stripped_package, "evosuite_test_case":evosuite_test_case}
    
    # print("Context : ", context)
    # Store replaced assertions for this method in the dictionary
    # replaced_assertions_per_method[method_name] = replaced_assertions
    
    # open file to write results
    if not os.path.exists(final_result_file):
        # If it doesn't exist, create the file with a header row
        with open(final_result_file, mode='w', newline='') as csv_file:
            # test_id, time, attempts, assertion_generated, is_compiled, is_run, mutation_score, CUT, MUT, project_dir, eo_assertions, 
            fieldnames = [
                "test_id", "execution_id", "oracle_type", "assertion_generated", "eo_assertions", "es_assertions",
                "eo_compiled_original", "eo_run_original", "eo_mutation_score_original", "eo_test_path_original",
                "es_compiled_original", "es_run_original", "es_mutation_score_original", "es_test_path_original",
                "eo_compiled_buggy", "eo_run_buggy", "eo_mutation_score_buggy", "eo_test_path_buggy",
                "es_compiled_buggy", "es_run_buggy", "es_mutation_score_buggy", "es_test_path_buggy",
                "total_time", "attempts", "assertion_generation_time", 
                "CUT", "MUT", "project_dir", "model", "used_developer_comments", "variant", 
                "prompts_and_responses", "timestamp"
            ]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

    # Get the current time in milliseconds
    start_time = time.perf_counter()
    
    result = {
        "attempts": None,
        "assertion_generated": None,
        "assertion_generation_time": None,
        "eo_assertions": None,
        
        # Original
        "eo_compiled_original": None,
        "eo_run_original": None,
        "eo_mutation_score_original": None,
        "eo_test_path_original": None,
        "es_compiled_original": None,
        "es_run_original": None,
        "es_mutation_score_original": None,
        "es_test_path_original": None,

        # Buggy
        "eo_compiled_buggy": None,
        "eo_run_buggy": None,
        "eo_mutation_score_buggy": None,
        "eo_test_path_buggy": None,
        "es_compiled_buggy": None,
        "es_run_buggy": None,
        "es_mutation_score_buggy": None,
        "es_test_path_buggy": None,
        
        "prompts_and_responses": None,
        "variant": None
    }
    result = generate_oracle_with_LLM(project_dir, context, (test_id+execution_id), llm_name, variant, consider_dev_comments, fix_run, fix_assertion)
    
    # if fix_run:
    #     return result
    
    end_time = time.perf_counter()

    total_time = (end_time - start_time) * 1000
    # Get the current timestamp as a string
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(final_result_file, mode='a', newline='') as csv_file:
        fieldnames = [
            "test_id", "execution_id", "oracle_type", "assertion_generated", "eo_assertions", "es_assertions",
            "eo_compiled_original", "eo_run_original", "eo_mutation_score_original", "eo_test_path_original",
            "es_compiled_original", "es_run_original", "es_mutation_score_original", "es_test_path_original",
            "eo_compiled_buggy", "eo_run_buggy", "eo_mutation_score_buggy", "eo_test_path_buggy",
            "es_compiled_buggy", "es_run_buggy", "es_mutation_score_buggy", "es_test_path_buggy",
            "total_time", "attempts", "assertion_generation_time", 
            "CUT", "MUT", "project_dir", "model", "used_developer_comments", "variant", 
            "prompts_and_responses", "timestamp"
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        # pretty print JSON
        prompts_and_responses = json.dumps(result["prompts_and_responses"], indent=2)

        oracle_type = Oracles.SIMPLE.name
        es_assertions = "\n".join(replaced_assertions)
        if es_assertions.startswith('fail'):
            oracle_type = Oracles.EXCEPTION.name

        writer.writerow({
            "test_id": test_id, 
            "execution_id": execution_id, 
            "oracle_type": oracle_type,
            "total_time": total_time,
            "attempts": result["attempts"], 
            "assertion_generated": result["assertion_generated"],
            "assertion_generation_time": result["assertion_generation_time"],
            "eo_assertions": result["eo_assertions"],
            "es_assertions": es_assertions,
            "eo_compiled_original": result["eo_compiled_original"],
            "eo_run_original": result["eo_run_original"],
            "eo_mutation_score_original": result["eo_mutation_score_original"],
            "eo_test_path_original": result["eo_test_path_original"],
            "es_compiled_original": result["es_compiled_original"],
            "es_run_original": result["es_run_original"],
            "es_mutation_score_original": result["es_mutation_score_original"],
            "es_test_path_original": result["es_test_path_original"],
            "eo_compiled_buggy": result["eo_compiled_buggy"],
            "eo_run_buggy": result["eo_run_buggy"],
            "eo_mutation_score_buggy": result["eo_mutation_score_buggy"],
            "eo_test_path_buggy": result["eo_test_path_buggy"],
            "es_compiled_buggy": result["es_compiled_buggy"],
            "es_run_buggy": result["es_run_buggy"],
            "es_mutation_score_buggy": result["es_mutation_score_buggy"],
            "es_test_path_buggy": result["es_test_path_buggy"],
            "CUT": class_under_test,
            "MUT": method_details_list,
            "project_dir": project_dir,
            "model": llm_name,
            "used_developer_comments": consider_dev_comments,
            "variant": result["variant"],
            "prompts_and_responses": prompts_and_responses,
            "timestamp": current_time,
        })
 
        print("Result generation: ", Fore.GREEN + "SUCCESS", Style.RESET_ALL)

    print("Oracle generation FINISHED")

    return result

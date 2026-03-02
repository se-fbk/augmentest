import csv
import math
import shutil
import os
import json

import javalang
import psutil
import re
import datetime

from src.common.string_tables import string_tables
from src.utils.utilities import ProjectUtilities

def find_processes_created_by(pid):
    """
    Find the process's and all subprocesses' pid
    """
    parent_process = psutil.Process(pid)
    child_processes = parent_process.children(recursive=True)
    pids = [process.pid for process in child_processes]
    return pids.append(pid)


def remove_imports(code):
    # Define the regular expression pattern
    pattern = r"^import.*;$\n"

    # Use re.sub to remove lines matching the pattern
    output_str = re.sub(pattern, "", code, flags=re.MULTILINE)

    return output_str


def get_latest_file(file_dir, rounds=None, suffix=None):
    """
    Get the latest file
    :param file_dir:
    :return:
    """
    all_files = os.listdir(file_dir)
    file_number = len([x for x in all_files if x.endswith(".json")])
    if not suffix:
        for file in all_files:
            if file.startswith(str(file_number) + "_"):
                return os.path.join(file_dir, file)
    else:
        if not rounds:
            rounds = math.floor(file_number / 3)
        for file in all_files:
            if file.endswith(suffix + "_" + str(rounds) + ".json"):
                return os.path.join(file_dir, file)
    return ""

def parse_file_name(filename):
    m_id, project_name, class_name, method_name, direction_and_test_num = filename.split('%')
    direction, test_num = direction_and_test_num.split('_')
    return m_id, project_name, class_name, method_name, direction, test_num.split('.')[0]


def parse_file_name(directory):
    dir_name = os.path.basename(directory)
    m_id, project_name, class_name, method_name, invalid = dir_name.split('%')
    return m_id, project_name, class_name, method_name

# def get_project_abspath():
#     return os.path.abspath(project_dir)


def remove_single_test_output_dirs(project_path):
    prefix = "test_"

    # Get a list of all directories in the current directory with the prefix
    directories = [d for d in os.listdir(project_path) if os.path.isdir(d) and d.startswith(prefix)]

    # Iterate through the directories and delete them if they are not empty
    for d in directories:
        try:
            shutil.rmtree(d)
            print(f"Directory {d} deleted successfully.")
        except Exception as e:
            print(f"Error deleting directory {d}: {e}")


def get_date_string(directory_name):
    return directory_name.split('%')[1]

def get_openai_content(content):
    """
    Get the content for OpenAI
    :param content:
    :return:
    """
    if not isinstance(content, dict):
        return ""
    return content["choices"][0]['message']["content"]


def get_openai_message(content):
    """
    Get the content for OpenAI
    :param content:
    :return:
    """
    if not isinstance(content, dict):
        return ""
    return content["choices"][0]['message']


def check_java_version():
    # java_home = os.environ.get('JAVA_HOME')
    # if 'jdk-17' in java_home:
    #     return 17
    # elif 'jdk-11' in java_home:
    #     return 11
    # else:
    return 11

def repair_package(code, package_info):
    """
    Repair package declaration in test.
    """
    first_line = code.split('import')[0]
    if package_info == '' or package_info in first_line:
        return code
    code = package_info + "\n" + code
    return code


# TODO: imports can be optimized
def repair_imports(code, imports):
    """
    Repair imports in test.
    """
    import_list = imports.split('\n')
    first_line, _code = code.split('\n', 1)
    for _import in reversed(import_list):
        if _import not in code:
            _code = _import + "\n" + _code
    return first_line + '\n' + _code


def add_timeout(test_case, timeout=8000):
    """
    Add timeout to test cases. Only for Junit 5
    """
    # check junit version
    junit4 = 'import org.junit.Test'
    junit5 = 'import org.junit.jupiter.api.Test'
    if junit4 in test_case:  # Junit 4
        test_case = test_case.replace('@Test(', f'@Test(timeout = {timeout}, ')
        return test_case.replace('@Test\n', f'@Test(timeout = {timeout})\n')
    elif junit5 in test_case:  # Junit 5
        timeout_import = 'import org.junit.jupiter.api.Timeout;'
        test_case = repair_imports(test_case, timeout_import)
        return test_case.replace('@Test\n', f'@Test\n    @Timeout({timeout})\n')
    else:
        print("Can not know which junit version!")
        return test_case


def export_method_test_case(output, class_name, method_test_case):
    """
    Export test case to file.
    output : pathto/project/testcase.java
    """
    # method_test_case = add_timeout(method_test_case)
    # f = os.path.join(output, class_name + "_" + str(m_id) + '_' + str(test_num) + "Test.java")

    f = os.path.join(output, class_name + ".java")
    if not os.path.exists(output):
        os.makedirs(output)
    with open(f, "w") as output_file:
        output_file.write(method_test_case)
        return f

def remove_test_case_artifacts(output, class_name):
    """
    Remove the .java source and .class compiled files for a given test case.
    """
    base_path = os.path.join(output, class_name)
    extensions = [".java", ".class"]
    removed_files = []

    for ext in extensions:
        file_path = base_path + ext
        if os.path.exists(file_path):
            os.remove(file_path)
            removed_files.append(file_path)

    return removed_files

def change_class_name(test_case, old_name, new_name):
    """
    Change the class name in the test_case by given m_id.
    """
    return test_case.replace(old_name, new_name, 1)


def get_current_time():
    """
    Get current time
    :return:
    """
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%H:%M:%S")
    return formatted_time

def remove_all_assertions_but_last(source_code):
    # Regular expression pattern to match assertions
    assertion_pattern = r'(\w+\.)?(assert|assertTrue|assertNull|fail|assertFalse|assertNotEquals|assertEquals|assertArrayEquals|assertNotNull|assertNotSame|assertSame|assertThat)\s*\(.+?\);'

    # Find all matches of the assertion pattern in the source_code
    assertions = re.findall(assertion_pattern, source_code)

    # If there are no assertions, return the source_code as is
    if not assertions:
        return source_code

    # Initialize the replaced_assertions list
    replaced_assertions = []

    # Remove all but the last assertion
    for i in range(len(assertions) - 1):
        source_code = re.sub(assertion_pattern, "", source_code, count=1)
        # replaced_assertions.append(assertions[i][0] + assertions[i][1] + "()")

    return source_code

def get_CUT_from_test_class_name(input_string):
    parts = input_string.split(string_tables.EVOSUITE_SIGNATURE)
    if len(parts) > 0:
        return parts[0]
    else:
        parts = input_string.split(string_tables.TEST_SIGNATURE)

        if len(parts) > 0:
            return parts[0]
        else:
            return input_string  # Return the original string if "_ESTest" or "Test" is not found

def get_MUT_from_string(input_string):
    parts = input_string.split(".")
    if len(parts) >= 2:
        return parts[1]
    else:
        return input_string  # Return the original string if there's no second part or it can't be split

def remove_key_value_pair_from_json(data, key):
    # Iterate through the list of dictionaries and remove key-value pairs
    for item in data:
        # Remove the 'dependencies' key if it exists in the current dictionary
        if key in item:
            del item[key]

    # Convert the modified data back to JSON (if needed)
    json_data = json.dumps(data, indent=2)
    return json_data

def write_entries_with_comments(context):
    # context = {"project_name", "class_name", "test_class_path", "test_class_name", 
    #        "test_method_name", "focal_method_details", "test_method_code", "assertion_placeholder", "test_case_with_placeholder", "package", "evosuite_test_case"}
    
    data = context.get("focal_method_details")
        
    comment_entries_file = "/home/shaker/evooracle_comments_entries.csv"
    # open file to write results
    if not os.path.exists(comment_entries_file):
        # If it doesn't exist, create the file with a header row
        with open(comment_entries_file, mode='w', newline='') as csv_file:
            
            fieldnames = ["project_name", "test_class_name", "test_method_name", "test_class_path", "dev_comments"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            
    # Iterate through the list of dictionaries and remove key-value pairs
    for item in data:
        # Remove the 'dependencies' key if it exists in the current dictionary
        if "dev_comments" in item:
            if item["dev_comments"]:
                with open(comment_entries_file, mode='a', newline='') as csv_file:
                    fieldnames = ["project_name", "test_class_name", "test_method_name", "test_class_path", "dev_comments"]
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    
                    writer.writerow({
                        "project_name": context.get("project_name"), 
                        "test_class_name": context.get("test_class_name"),  
                        "test_method_name": context.get("test_method_name"), 
                        "test_class_path": context.get("test_class_path"),  
                        "dev_comments": item["dev_comments"],
                    })
                break
    

def remove_empty_lines(input_text):
    lines = input_text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    result = '\n'.join(non_empty_lines)
    return result

def replace_assertions(source_code):
    # Regular expression pattern to match assertions
    # Define the assertions to be replaced
    assertion_patterns = [
        r'(\w+\.)?assert\s*\(.+?\);',           # Matches ClassName.assert(...)
        r'(\w+\.)?assertTrue\s*\(.+?\);',       # Matches ClassName.assertTrue(...)
        r'(\w+\.)?assertNull\s*\(.+?\);',       # Matches ClassName.assertNull(...)
        r'(\w+\.)?fail\s*\(.+?\);',             # Matches ClassName.fail(...)
        r'(\w+\.)?assertFalse\s*\(.+?\);',      # Matches ClassName.assertFalse(...)
        r'(\w+\.)?assertNotEquals\s*\(.+?\);',  # Matches ClassName.assertNotEquals(...)
        r'(\w+\.)?assertEquals\s*\(.+?\);',     # Matches ClassName.assertEquals(...)
        r'(\w+\.)?assertArrayEquals\s*\(.+?\);',# Matches ClassName.assertArrayEquals(...)
        r'(\w+\.)?assertNotNull\s*\(.+?\);',    # Matches ClassName.assertNotNull(...)
        r'(\w+\.)?assertNotSame\s*\(.+?\);',    # Matches ClassName.assertNotSame(...)
        r'(\w+\.)?assertSame\s*\(.+?\);',       # Matches ClassName.assertSame(...)
        r'(\w+\.)?assertThat\s*\(.+?\);',       # Matches ClassName.assertThat(...)
    ]

    # List to store replaced assertions for this method
    replaced_assertions = []

    # Replace assertions with the placeholder
    for pattern in assertion_patterns:
        def replacement(match):
            # Get the matched text
            matched_text = match.group(0)
            # print(f"Pattern: {pattern}")
            # print(f"Replaced: {matched_text}")
            replaced_assertions.append(matched_text)
            return (string_tables.ASSERTION_PLACEHOLDER)

        source_code = re.sub(pattern, replacement, source_code)

    return source_code, replaced_assertions

def extract_assertions_from_string(input_string):
    # Regular expression pattern to match assertions
    assertion_patterns = [
        r'(\w+\.)?assert\s*\(.+?\);',           # Matches ClassName.assert(...)
        r'(\w+\.)?assertTrue\s*\(.+?\);',       # Matches ClassName.assertTrue(...)
        r'(\w+\.)?assertNull\s*\(.+?\);',       # Matches ClassName.assertNull(...)
        r'(\w+\.)?fail\s*\(.+?\);',             # Matches ClassName.fail(...)
        r'(\w+\.)?assertFalse\s*\(.+?\);',      # Matches ClassName.assertFalse(...)
        r'(\w+\.)?assertNotEquals\s*\(.+?\);',  # Matches ClassName.assertNotEquals(...)
        r'(\w+\.)?assertEquals\s*\(.+?\);',     # Matches ClassName.assertEquals(...)
        r'(\w+\.)?assertArrayEquals\s*\(.+?\);',# Matches ClassName.assertArrayEquals(...)
        r'(\w+\.)?assertNotNull\s*\(.+?\);',    # Matches ClassName.assertNotNull(...)
        r'(\w+\.)?assertNotSame\s*\(.+?\);',    # Matches ClassName.assertNotSame(...)
        r'(\w+\.)?assertSame\s*\(.+?\);',       # Matches ClassName.assertSame(...)
        r'(\w+\.)?assertThat\s*\(.+?\);',       # Matches ClassName.assertThat(...)
    ]

    # List to store extracted assertions
    extracted_assertions = []

    # Iterate through each pattern and find matches in the input string
    for pattern in assertion_patterns:
        matches = re.finditer(pattern, input_string)
        for match in matches:
            extracted_assertions.append(match.group(0))

    extracted_assertions = '\n'.join(extracted_assertions)
    return extracted_assertions


def extract_first_assertion_from_string_old(input_string):
    # Regular expression pattern to match assertions
    assertion_patterns = [
        r'(\w+\.)?assert\s*\(.+?\);',           # Matches ClassName.assert(...)
        r'(\w+\.)?assertTrue\s*\(.+?\);',       # Matches ClassName.assertTrue(...)
        r'(\w+\.)?assertNull\s*\(.+?\);',       # Matches ClassName.assertNull(...)
        r'(\w+\.)?fail\s*\(.+?\);',             # Matches ClassName.fail(...)
        r'(\w+\.)?assertFalse\s*\(.+?\);',      # Matches ClassName.assertFalse(...)
        r'(\w+\.)?assertNotEquals\s*\(.+?\);',  # Matches ClassName.assertNotEquals(...)
        r'(\w+\.)?assertEquals\s*\(.+?\);',     # Matches ClassName.assertEquals(...)
        r'(\w+\.)?assertArrayEquals\s*\(.+?\);',# Matches ClassName.assertArrayEquals(...)
        r'(\w+\.)?assertNotNull\s*\(.+?\);',    # Matches ClassName.assertNotNull(...)
        r'(\w+\.)?assertNotSame\s*\(.+?\);',    # Matches ClassName.assertNotSame(...)
        r'(\w+\.)?assertSame\s*\(.+?\);',       # Matches ClassName.assertSame(...)
        r'(\w+\.)?assertThat\s*\(.+?\);',       # Matches ClassName.assertThat(...)
    ]

    # Iterate through each pattern and find matches in the input string
    for pattern in assertion_patterns:
        match = re.search(pattern, input_string)
        if match:
            return match.group(0)

    
    return ""

def extract_first_assertion_from_string(input_string):
    # Regular expression pattern to match assertions with balanced parentheses and a semicolon at the end
    assertion_patterns = [
        r'(\w+\.)?assert\s*\((?:[^()]*|\([^()]*\))*\);?',           # Matches ClassName.assert(...)
        r'(\w+\.)?assertTrue\s*\((?:[^()]*|\([^()]*\))*\);?',       # Matches ClassName.assertTrue(...)
        r'(\w+\.)?assertNull\s*\((?:[^()]*|\([^()]*\))*\);?',       # Matches ClassName.assertNull(...)
        r'(\w+\.)?fail\s*\((?:[^()]*|\([^()]*\))*\);?',             # Matches ClassName.fail(...)
        r'(\w+\.)?assertFalse\s*\((?:[^()]*|\([^()]*\))*\);?',      # Matches ClassName.assertFalse(...)
        r'(\w+\.)?assertNotEquals\s*\((?:[^()]*|\([^()]*\))*\);?',  # Matches ClassName.assertNotEquals(...)
        r'(\w+\.)?assertEquals\s*\((?:[^()]*|\([^()]*\))*\);?',     # Matches ClassName.assertEquals(...)
        r'(\w+\.)?assertArrayEquals\s*\((?:[^()]*|\([^()]*\))*\);?',# Matches ClassName.assertArrayEquals(...)
        r'(\w+\.)?assertNotNull\s*\((?:[^()]*|\([^()]*\))*\);?',    # Matches ClassName.assertNotNull(...)
        r'(\w+\.)?assertNotSame\s*\((?:[^()]*|\([^()]*\))*\);?',    # Matches ClassName.assertNotSame(...)
        r'(\w+\.)?assertSame\s*\((?:[^()]*|\([^()]*\))*\);?',       # Matches ClassName.assertSame(...)
        r'(\w+\.)?assertThat\s*\((?:[^()]*|\([^()]*\))*\);?',       # Matches ClassName.assertThat(...)
    ]

    # Iterate through each pattern and find matches in the input string
    for pattern in assertion_patterns:
        match = re.search(pattern, input_string)
        if match:
            assertion = match.group(0)
            # Ensure the assertion ends with a semicolon
            if not assertion.endswith(';'):
                assertion += ';'
            return assertion

    return ""

def extract_first_assertion(input_string):
    # Regular expression pattern to match any assertion starting with the keywords and ending with a semicolon
    pattern = r'\b(assert(?:True|False|Null|NotNull|Equals|NotEquals|Same|NotSame|ArrayEquals|That)?|fail)\b[^;]*;'
    
    match = re.search(pattern, input_string)
    if match:
        return match.group(0)
    
    return ""

def extract_code_block_statements(input_string):
    # Regular expression pattern to capture the content between optional code block delimiters
    code_block_pattern = r'(?:```(?:\w+)?\s*\n|`{1}\s*\n)?(.*?)(?:\n```|`{1}|$)'

    # Search for the code block in the input string
    match = re.search(code_block_pattern, input_string, re.DOTALL)
    
    if match:
        code_block_content = match.group(1).strip()
        
        # Regular expression pattern to validate the assertion statement
        assertion_pattern = r'^(?:\w+\.)?(?:assertTrue|assertFalse|assertNull|assertNotNull|assertNotSame|assertSame|assertThat|assertArrayEquals|assertNotEquals|assertEquals|fail)\s*\(.+\);$'
        
        # Check if the extracted content matches the assertion pattern
        if re.match(assertion_pattern, code_block_content):
            return code_block_content

    return ""

def extract_assert_statements(input_string):
    # Define a regex pattern to match code blocks, single backticks, or unformatted text
    code_block_pattern = r'```(?:java|[\w]+)?\s*(.*?)\s*```|`(.*?)`|(?:(?<=\s)|^)(.*?)(?=\n\n|\Z)'
    
    # Define a regex pattern to match assert statements including fail
    assertion_pattern = r'\bassert(?:True|False|Equals|NotEquals|ArrayEquals|NotNull|NotSame|Same|That)?\s*\((?:[^()]*|\([^()]*\))*\);|fail\s*\((?:[^()]*|\([^()]*\))*\);'

    # Search for code blocks or standalone code
    code_blocks = re.findall(code_block_pattern, input_string, re.DOTALL)
    
    assertions = []
    
    for block in code_blocks:
        # Select the actual code block content
        code_content = block[0] if block[0] else block[1] if block[1] else block[2]
        # Find all assertions in the code block
        matches = re.findall(assertion_pattern, code_content)
        assertions.extend(matches)
    
    return assertions[0]

def semicolonFormatter(statement):
    """
    Adds a semicolon at the end of the statement if it does not already end with one.
    
    Parameters:
    statement (str): The input string to format.
    
    Returns:
    str: The input string with a semicolon at the end if it wasn't there already.
    """
    # Strip any leading or trailing whitespace for consistency
    statement = statement.strip()
    
    # Check if the string ends with a semicolon
    if not statement.endswith(';'):
        # Append a semicolon if it does not end with one
        statement += ';'
    
    return statement

def extract_complex_assertion(statement):
    # Define possible assertion keywords
    assertion_keywords = ["assert", "assertTrue", "assertNull", "fail", "assertFalse", "assertNotEquals", "assertEquals", "assertArrayEquals", "assertNotNull", "assertNotSame", "assertSame", "assertThat", "assertThrows"]
    
    # Iterate through the statement to find assertion keywords
    for keyword in assertion_keywords:
        keyword_lower = keyword.lower()
        start_index = 0
        
        while True:
            start_index = statement.lower().find(keyword_lower, start_index)
            if start_index == -1:
                break
            
            # Move past the keyword
            start_index += len(keyword)
            while start_index < len(statement) and statement[start_index].isspace():
                start_index += 1
            
            # Check if it is followed by an opening parenthesis
            if start_index < len(statement) and statement[start_index] == '(':
                # Track parentheses to find the matching closing parenthesis
                open_parens = 1
                end_index = start_index + 1
                
                while end_index < len(statement) and open_parens > 0:
                    if statement[end_index] == '(':
                        open_parens += 1
                    elif statement[end_index] == ')':
                        open_parens -= 1
                    end_index += 1
                
                # Check for a trailing semicolon
                if end_index < len(statement) and statement[end_index] == ';':
                    end_index += 1
                
                # Extract and return the assertion statement
                return statement[start_index - len(keyword):end_index].strip()
            
            # Move to the next occurrence
            start_index += len(keyword)
    
    return ''

def extract_simple_assertion(statement):
    """
    Extracts simple assertion statements such as 'assert true;', 'assert false', and 'assert false;'
    from within a larger text block.
    
    Parameters:
    statement (str): The input string to extract assertion from.
    
    Returns:
    str: The extracted assertion statement, or an empty string if no assertion is found.
    """
    # Normalize the statement for consistent comparison
    statement = statement.strip()
    
    # Define the possible assertion patterns with optional semicolon
    assertion_patterns = [
        r"\bassert true\b;?",
        r"\bassert false\b;?"
    ]
    
    # Check for the patterns
    for pattern in assertion_patterns:
        # Use regex to find patterns anywhere in the statement
        match = re.search(pattern, statement)
        if match:
            # Return the match with a semicolon if it's not present
            return match.group() if match.group().endswith(';') else f"{match.group()};"
    
    # If no match found, return an empty string
    return ''

def prepare_temp_test_and_check_compilation(test_suite_source_code, output_path, class_name, test_num, method_name, project_name, package, original_project_dir):
    """
    Prepare temp TestSuite and compile it
    :param project_name:
    :param test_num:
    :param method_id:
    :param class_name:
    :param input_string:
    :param output_path:
    :return:
    """

    # preparing temp TestSuite
    temp_test_suite = class_name + '_' + str(test_num) + string_tables.AUGMENTEST_SIGNATURE
    temp_test_suite_source_code = change_class_name(test_suite_source_code, class_name, temp_test_suite)


    # export temp test case
    temp_out_dir = os.path.dirname(output_path)
    temp_test_file_name = export_method_test_case(temp_out_dir, temp_test_suite, temp_test_suite_source_code)

    original_response_dir = os.path.abspath(temp_out_dir)
    original_target_dir = os.path.abspath(original_project_dir)

    # compile test
    is_compiled = ProjectUtilities.compile_test_suite(original_response_dir, original_target_dir, temp_test_file_name, package, temp_test_suite)

    # clean temp test
    remove_test_case_artifacts(temp_out_dir, temp_test_suite)

    return is_compiled


def compile_test_case(test_suite_source_code, output_path, class_name, package, original_project_dir):
    """
    Prepare temp TestSuite and compile it
    :param test_suite_source_code:
    :param test_num:
    :param class_name:
    :param output_path:
    :return:
    """

    # preparing temp TestSuite
    # temp_test_suite = class_name + '_' + str(test_num) + string_tables.EVOORACLE_SIGNATURE


    # export temp test case
    temp_out_dir = os.path.dirname(output_path)
    temp_test_file_name = export_method_test_case(temp_out_dir, class_name, test_suite_source_code)

    original_response_dir = os.path.abspath(temp_out_dir)
    original_target_dir = os.path.abspath(original_project_dir)

    # compile test
    is_compiled, compilation_logs = ProjectUtilities.compile_test_suite(original_response_dir, original_target_dir, temp_test_file_name, package, class_name)

    # clean temp test
    remove_test_case_artifacts(temp_out_dir, class_name)

    return is_compiled, compilation_logs


def compile_and_run_test_case(test_suite_source_code, output_path, class_name, package, original_project_dir):
    """
    Prepare temp TestSuite, compile it, run it
    :param test_suite_source_code:
    :param test_num:
    :param class_name:
    :param output_path:
    :return:
    """

    # preparing temp TestSuite
    # temp_test_suite = class_name + '_' + str(test_num) + string_tables.EVOORACLE_SIGNATURE
    is_run, run_logs = None, None

    # export temp test case
    temp_out_dir = os.path.dirname(output_path)
    temp_test_file_name = export_method_test_case(temp_out_dir, class_name, test_suite_source_code)

    original_response_dir = os.path.abspath(temp_out_dir)
    original_target_dir = os.path.abspath(original_project_dir)

    # compile test
    is_compiled, compilation_logs = ProjectUtilities.compile_test_suite(original_response_dir, original_target_dir,
                                                                        temp_test_file_name, package, class_name)

    if is_compiled:
        is_run, run_logs = ProjectUtilities.execute_test_suite(original_response_dir, original_target_dir,
                                                               temp_test_file_name,
                                                               package, class_name)

    # clean temp test
    remove_test_case_artifacts(temp_out_dir, class_name)

    return is_compiled, compilation_logs, is_run, run_logs

def extract_and_run(evooracle_source_code, output_path, class_name, test_num, method_name, project_name, package, original_project_dir):
    """
    Extract the code and run it
    :param project_name:
    :param test_num:
    :param method_id:
    :param class_name:
    :param input_string:
    :param output_path:
    :return:
    """
    result = {}
    validation_result = {
        "eo_compiled_original": False,
        "eo_run_original": False,
        "eo_mutation_score_original": 0,
        "eo_test_path_original": None,
        "prompts_and_responses": None,
    }

    has_code, extracted_code, has_syntactic_error = extract_code(evooracle_source_code)
    if not has_code:
        return validation_result
    result["has_code"] = has_code
    result["source_code"] = extracted_code
    if package:
        result["source_code"] = repair_package(extracted_code, package)
    result["has_syntactic_error"] = has_syntactic_error


    # print("Project Name: " + project_name)
    # print("Class Name: " + class_name)

    renamed_class_evooracle = class_name + '_' + str(test_num) + string_tables.AUGMENTEST_SIGNATURE
    renamed_class_source_code_evooracle = change_class_name(extracted_code, class_name, renamed_class_evooracle)


    # process for Original Project
    original_out_dir = os.path.dirname(output_path)
    original_evooracle_test_file_name = export_method_test_case(original_out_dir, renamed_class_evooracle, renamed_class_source_code_evooracle)

    original_response_dir = os.path.abspath(original_out_dir)
    original_target_dir = os.path.abspath(original_project_dir)

    # run test

    o_test_result_eo_c, o_test_result_eo_r, o_test_result_eo_ms = ProjectUtilities.execute_test_suite(original_response_dir, original_target_dir, original_evooracle_test_file_name, package, renamed_class_evooracle)

    # 3. Read the result

    # Original Project results
    validation_result["eo_compiled_original"] = o_test_result_eo_c
    validation_result["eo_run_original"] = o_test_result_eo_r
    validation_result["eo_mutation_score_original"] = o_test_result_eo_ms
    validation_result["eo_test_path_original"] = original_evooracle_test_file_name

    return validation_result

def extract_code(string):
    """
    Check if the string is valid code and extract it.
    :param string:
    :return: has_code, extracted_code, has_syntactic_error
    """
    # if the string is valid code, return True
    if is_syntactically_correct(string):
        return True, string, False

    has_code = False
    extracted_code = ""
    has_syntactic_error = False

    # Define regex pattern to match the code blocks
    pattern = r"```[java]*([\s\S]*?)```"

    # Find all matches in the text
    matches = re.findall(pattern, string)
    if matches:
        # Filter matches to only include ones that contain "@Test"
        filtered_matches = [match.strip() for match in matches if
                            "@Test" in match and "class" in match and "import" in match]
        if filtered_matches:
            for match in filtered_matches:
                has_syntactic_error, extracted_code = syntactic_check(match)
                if extracted_code != "":
                    has_code = True
                    break

    if not has_code:
        if "```java" in string:
            separate_string = string.split("```java")[1]
            if "@Test" in separate_string:
                has_syntactic_error, temp_code = syntactic_check(separate_string)
                if temp_code != "":
                    extracted_code = temp_code
                    has_code = True
        elif "```" in string:
            separate_strings = string.split("```")
            for separate_string in separate_strings:
                if "@Test" in separate_string:
                    has_syntactic_error, temp_code = syntactic_check(separate_string)
                    if temp_code != "":
                        extracted_code = temp_code
                        has_code = True
                        break
        else:  # Define boundary
            allowed = ["import", "packages", "", "@"]
            code_lines = string.split("\n")
            start, anchor, end = -1, -1, -1
            allowed_lines = [False for _ in range(len(code_lines))]
            left_brace = {x: 0 for x in range(len(code_lines))}
            right_brace = {x: 0 for x in range(len(code_lines))}
            for i, line in enumerate(code_lines):
                left_brace[i] += line.count("{")
                right_brace[i] += line.count("}")
                striped_line = line.strip()

                for allow_start in allowed:
                    if striped_line.startswith(allow_start):
                        allowed_lines[i] = True
                        break

                if re.search(r'public class .*Test', line) and anchor == -1:
                    anchor = i

            if anchor != -1:
                start = anchor
                while start:
                    if allowed_lines[start]:
                        start -= 1

                end = anchor
                left_sum, right_sum = 0, 0
                while end < len(code_lines):
                    left_sum += left_brace[end]
                    right_sum += right_brace[end]
                    if left_sum == right_sum and left_sum >= 1 and right_sum >= 1:
                        break
                    end += 1

                temp_code = "\n".join(code_lines[start:end + 1])
                has_syntactic_error, temp_code = syntactic_check(temp_code)
                if temp_code != "":
                    extracted_code = temp_code
                    has_code = True

    extracted_code = extracted_code.strip()
    return has_code, extracted_code, has_syntactic_error

def syntactic_check(code):
    """
    Syntactic repair
    :param code:
    :return: has_syntactic_error, code
    """
    if is_syntactically_correct(code):
        return False, code
    else:
        stop_point = [";", "}", "{", " "]  # Stop point
        for idx in range(len(code) - 1, -1, -1):
            if code[idx] in stop_point:
                code = code[:idx + 1]
                break
        left_bracket = code.count("{")
        right_bracket = code.count("}")
        for idx in range(left_bracket - right_bracket):
            code += "}\n"

        if is_syntactically_correct(code):
            return True, code

        matches = list(re.finditer(r"(?<=\})[^\}]+(?=@)", code))
        if matches:
            code = code[:matches[-1].start() + 1]
            left_count = code.count("{")
            right_count = code.count("}")
            for _ in range(left_count - right_count):
                code += "\n}"
        if is_syntactically_correct(code):
            return True, code
        else:
            return True, ""

def is_syntactically_correct(code):
    """
    Check if the code is syntactically correct
    :param code:
    :return:
    """
    try:
        javalang.parse.parse(code)
        return True, None
    except Exception as e:
        return False, str(e)
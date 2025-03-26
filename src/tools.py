import csv
import math
import shutil
import sys
from config import *
import os
import json
import psutil
import re
import tiktoken
import datetime

from string_tables import string_tables

enc = tiktoken.get_encoding("cl100k_base")
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


def get_messages_tokens(messages):
    """
    Get the tokens of messages.
    :param messages: The messages.
    :return: The tokens.
    """
    cnt = 0
    for message in messages:
        cnt += count_tokens(message)
    return cnt


def count_tokens(strings):
    tokens = encoding.encode(strings)
    cnt = len(tokens)
    return cnt


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


def get_dataset_path(method_id, project_name, class_name, method_name, direction):
    """
    Get the dataset path
    :return:
    """
    if direction == "raw":
        return os.path.join(dataset_dir, "raw_data",
                            method_id + "%" + project_name + "%" + class_name + "%" + method_name + "%raw.json")
    return os.path.join(dataset_dir, "direction_" + str(direction),
                        method_id + "%" + project_name + "%" + class_name + "%" + method_name + "%d" + str(
                            direction) + ".json")


def get_project_class_info(method_id, project_name, class_name, method_name):
    file_name = get_dataset_path(method_id, project_name, class_name, method_name, "raw")
    if os.path.exists(file_name):
        with open(file_name, "w") as f:
            raw_data = json.load(f)
        return raw_data["package"], raw_data["imports"]
    return None, None


def parse_file_name(filename):
    m_id, project_name, class_name, method_name, direction_and_test_num = filename.split('%')
    direction, test_num = direction_and_test_num.split('_')
    return m_id, project_name, class_name, method_name, direction, test_num.split('.')[0]


def parse_file_name(directory):
    dir_name = os.path.basename(directory)
    m_id, project_name, class_name, method_name, invalid = dir_name.split('%')
    return m_id, project_name, class_name, method_name


def get_raw_data(method_id, project_name, class_name, method_name):
    with open(get_dataset_path(method_id, project_name, class_name, method_name, "raw"), "r") as f:
        raw_data = json.load(f)
    return raw_data


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


def find_result_in_projects():
    """
    Find the new directory.
    :return: The new directory.
    """
    all_results = [x for x in os.listdir(project_dir) if '%' in x]
    all_results = sorted(all_results, key=get_date_string)
    return os.path.join(result_dir, all_results[-1])


def find_newest_result():
    """
    Find the newest directory.
    :return: The new directory.
    """
    all_results = os.listdir(result_dir)
    all_results = sorted(all_results, key=get_date_string)
    return os.path.join(result_dir, all_results[-1])


def get_finished_project():
    projects = []
    all_directory = os.listdir(result_dir)
    for directory in all_directory:
        if directory.startswith("scope_test"):
            sub_dir = os.path.join(result_dir, directory)
            child_dir = ""
            for dir in os.listdir(sub_dir):
                if os.path.isdir(os.path.join(sub_dir, dir)):
                    child_dir = dir
                    break
            m_id, project_name, class_name, method_name = parse_file_name(child_dir)
            if project_name not in projects:
                projects.append(project_name)
    return projects


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
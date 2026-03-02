import os.path
import os
import shutil
import sys

from src.config.config import *
from src.utils.tools import *
from src.preprocessing.parse_data import parse_data
from src.utils.utilities import ProjectUtilities
from colorama import Fore, Style
from typing import TypedDict, Any, List
from src.common.resource_manager import ResourceManager
from src.config.config import *
from src.utils.tools import *
from src.common.string_tables import string_tables


# --- NEW TYPEDDICT FOR CONTEXT KEYS (Provides Autocomplete) ---
# Note: All values are defined as 'str' because they are converted to
# JSON strings, string booleans, or plain strings before being returned.
class ContextKeys(TypedDict):
    project_name: str
    class_name: str # CUT name
    fields: str     # CUT fields
    test_class_path: str
    test_class_name: str
    test_method_name: str
    focal_method_details: str # JSON String
    class_method_details: str # JSON String
    test_method_code: str
    assertion_placeholder: str
    test_case_with_placeholder: str
    package: str # Stripped package
    evosuite_test_case: str

    # --- New Keys ---
    test_class_has_constructor: str     # Boolean as string ("True"/"False")
    test_class_contains_test: str       # Boolean as string ("True"/"False")
    test_class_methods: str             # Full list of test class methods (JSON String)
    replaced_assertions_list: str       # List of replaced assertions (JSON String)
    cut_all_methods: str                # Full list of all CUT methods (JSON String)
    focal_method_names: str             # Simple list of MUT names (JSON String)
    raw_focal_methods_from_db: str      # Raw list of focal method names (JSON String)
    test_class_imports: str
    test_class_signature: str
    test_class_super_class: str
    test_class_full_fields: str
    test_class_dependencies: str
    test_class_argument_list: str
    test_class_interfaces: str
    test_method_code_original: str
    test_method_code_no_assertions_but_last: str
    cut_class_name: str                 # The CUT name (redundant with 'class_name' but kept for completeness)
    cut_signature: str
    cut_super_class: str
    cut_package: str
    cut_imports: str
    cut_dependencies: str
# --- END TYPEDDICT ---

def clean_output_directory(project_path):
    """
    Remove all contents from the output directory.
    :param project_path: Root directory of the project
    :return: None
    """
    output_path = project_path + output_dir
    # Remove the dataset directory if it exists
    if os.path.exists(output_path):
        shutil.rmtree(output_path)


def execute_processing(project_path, programming_language):
    # Clear any previous output
    clean_output_directory(project_path)

    #Compile project
    is_compiled_project, logs = ProjectUtilities.compile_project(project_path)

    if not is_compiled_project:
        print(Fore.RED + "ERROR: AugmenTest cannot proceed as the project has compilation errors.", Style.RESET_ALL)
        sys.exit(1)

    # Analyze project structure
    metadata_path = ProjectUtilities.analyze_project(project_path, programming_language)

    # Extract and process data
    parse_data(project_path, metadata_path,
               (project_path + db_json_file),
               (project_path + db_csv_file))

def build_test_case(
    package: str,
    imports: str,
    signature: str,
    source_code: str,
) -> str:
    """
    Builds a full Java test case by wrapping the
    given method source inside the class structure.

    Args:
        package: Java package declaration
        imports: Import statements
        signature: Class signature (e.g., 'public class FooTest')
        source_code: Test method source code

    Returns:
        Full Java test case as a string.
    """
    return (
        package
        + string_tables.NL
        + imports
        + string_tables.NL
        + signature
        + string_tables.NL
        + string_tables.LEFT_CURLY_BRACE
        + string_tables.NL
        + source_code
        + string_tables.NL
        + string_tables.RIGHT_CURLY_BRACE
    )


def build_context_for_test_case(project_dir: str, class_name: str, method_name: str) -> ContextKeys:
    project_name: str = os.path.basename(os.path.normpath(project_dir))

    # --- 1. Get Test Class Details ---
    manager: ResourceManager = ResourceManager(project_dir + db_json_file)

    class_details: dict[str, Any] = manager.get_class_details_from_projectname_classname(project_name, class_name)

    # All fields retrieved from class_details
    signature: str = class_details.get("signature", "")
    super_class: str = class_details.get("super_class", "")
    package: str = class_details.get("package", "")
    stripped_package: str = class_details.get("package", "").split(' ')[1].strip(';')
    imports: str = class_details.get("imports", "")
    fields: str = class_details.get("fields", "")
    has_constructor: bool = class_details.get("has_constructor", False) # bool
    contains_test: bool = class_details.get("contains_test", False)     # bool
    dependencies: str = class_details.get("dependencies", "")
    methods: List[dict[str, Any]] = class_details.get("methods", [])    # list
    argument_list: str = class_details.get("argument_list", "")
    interfaces: str = class_details.get("interfaces", "")
    test_class_name: str = class_details.get("class_name", "")
    test_class_path: str = class_details.get("class_path", "")

    # --- 2. Get Test Method Details & Process Code ---
    test_method_details: dict[str, Any] = manager.get_details_by_project_class_and_method(project_name, test_class_name, method_name,
                                                                          False)
    focal_methods_list: List[str] = test_method_details.get("focal_methods", [])  # list[str]
    source_code: str = test_method_details.get("source_code", "")
    original_source_code: str = source_code  # Store the original for context

    # Prepare versions of the test code
    source_code_no_assertions_but_last: str = remove_all_assertions_but_last(source_code)
    source_code_no_assertions_but_last = remove_empty_lines(source_code_no_assertions_but_last)
    evosuite_test_case: str = build_test_case(package, imports, signature,
                                         source_code_no_assertions_but_last)  # Using the code with only last assertion

    source_code_with_placeholder: str
    replaced_assertions: List[str]
    source_code_with_placeholder, replaced_assertions = replace_assertions(source_code)
    source_code_with_placeholder = remove_empty_lines(source_code_with_placeholder)

    test_case_with_placeholder: str = build_test_case(package, imports, signature, source_code_with_placeholder)

    test_method_details["source_code_with_placeholder"] = source_code_with_placeholder

    # --- 3. Get Class Under Test (CUT) Details ---
    # class_under_test: str = get_CUT_from_test_class_name(test_class_name)
    class_under_test = re.sub(r'_?ESTest$|Test$|Tests$', '', test_class_name)

    # if class_under_test == test_class_name:
    #     # No test suffix found, might be a different naming pattern
    #     return None

    class_under_test_details: dict[str, Any] = manager.get_class_details_from_projectname_classname(project_name, class_under_test)

    class_under_test_fields: str = class_under_test_details.get("fields", "")
    class_under_test_fields = remove_empty_lines(class_under_test_fields)

    # All fields retrieved from CUT details
    cut_methods: List[dict[str, Any]] = class_under_test_details.get("methods", []) # list
    cut_dependencies: str = class_under_test_details.get("dependencies", "")
    cut_signature: str = class_under_test_details.get("signature", "")
    cut_super_class: str = class_under_test_details.get("super_class", "")
    cut_package: str = class_under_test_details.get("package", "").split(' ')[1].strip(';')
    cut_imports: str = class_under_test_details.get("imports", "")
    cut_class_name: str = class_under_test_details.get("class_name", "")  # The CUT name itself

    # --- 4. Get Methods Under Test (MUT) Details ---
    mut_list: set = set()
    for focal_method in focal_methods_list:
        mut: str = get_MUT_from_string(focal_method)
        mut_list.add(mut)
    mut_list: List[str] = list(mut_list) # list[str]

    method_details_list: List[dict[str, Any]] = []
    for MUT in mut_list:
        method_details: dict[str, Any] = manager.get_details_by_project_class_and_method(project_name, class_under_test, MUT, True)
        if method_details:
            method_details_list.append(method_details)

    # Store as the original key expects a JSON string
    focal_method_details: str = json.dumps(method_details_list, indent=2)

    # --- 5. Get Other CUT Method Details ---
    class_method_comments_list: List[dict[str, str]] = []
    for class_method in cut_methods:
        # Check if the parameters match any focal method, only add if NOT a focal method
        is_focal: bool = any(
            foc_method.get("parameters") == class_method.get("parameters")
            for foc_method in method_details_list
        )

        if not is_focal:
            details: dict[str, str] = {
                "method_name": class_method.get("method_name", ""),
                "developer_comments": class_method.get("dev_comments", ""),
                "return_type": class_method.get("return_type", ""),
            }
            class_method_comments_list.append(details)

    # Store as the original key expects a JSON string
    class_method_list: str = json.dumps(class_method_comments_list, indent=2)

    # --- 6. Build the Final Context Dictionary with ALL Fields ---
    # The final dictionary is explicitly typed as ContextKeys to enable autocomplete
    context: ContextKeys = {
        # --- ORIGINAL KEYS ---
        "project_name": project_name,
        "class_name": class_under_test,
        "fields": class_under_test_fields,
        "test_class_path": test_class_path,
        "test_class_name": test_class_name,
        "test_method_name": method_name,
        "focal_method_details": focal_method_details,
        "class_method_details": class_method_list,
        "test_method_code": source_code_with_placeholder,
        "assertion_placeholder": string_tables.ASSERTION_PLACEHOLDER,
        "test_case_with_placeholder": test_case_with_placeholder,
        "package": stripped_package,
        "evosuite_test_case": evosuite_test_case,

        # --- NEW KEYS ---
        "test_class_has_constructor": str(has_constructor),
        "test_class_contains_test": str(contains_test),

        # Lists converted to JSON strings
        "test_class_methods": json.dumps(methods, indent=2),
        "replaced_assertions_list": json.dumps(replaced_assertions, indent=2),
        "cut_all_methods": json.dumps(cut_methods, indent=2),
        "focal_method_names": json.dumps(mut_list, indent=2),
        "raw_focal_methods_from_db": json.dumps(focal_methods_list, indent=2),

        # Other New Keys
        "test_class_imports": imports,
        "test_class_signature": signature,
        "test_class_super_class": super_class,
        "test_class_full_fields": fields,
        "test_class_dependencies": dependencies,
        "test_class_argument_list": argument_list,
        "test_class_interfaces": interfaces,
        "test_method_code_original": original_source_code,
        "test_method_code_no_assertions_but_last": source_code_no_assertions_but_last,
        "cut_class_name": cut_class_name,
        "cut_signature": cut_signature,
        "cut_super_class": cut_super_class,
        "cut_package": cut_package,
        "cut_imports": cut_imports,
        "cut_dependencies": cut_dependencies,
    }

    return context
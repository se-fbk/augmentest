# ---------------------------------------------------------
# Script: Test Case Preprocessor
# Developer: Shaker Mahmud Khandaker
# Project: AugmenTest
# Last Updated: March 18, 2025
# Purpose: Processes test cases and creates JSON structures 
#          containing Class and Method metadata.
# ---------------------------------------------------------

import os
import sys
from tools import *
from parse_data import parse_data
from test_processor import prepare_test_cases_entries
from utilities import ProjectUtilities
from colorama import Fore, Style

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

    # Analyze project structure
    metadata_path = ProjectUtilities.analyze_project(project_path, programming_language)
    
    # Extract and process data
    parse_data(project_path, metadata_path, 
              (project_path + db_json_file), 
              (project_path + db_csv_file))

    # Generate test case entries
    prepare_test_cases_entries(project_path)
    
if __name__ == '__main__':
    # Verify command-line arguments
    if len(sys.argv) > 2:
        project_path = sys.argv[1]
        programming_language = sys.argv[2].upper()
        print(Style.BRIGHT + "Project Directory: " + Style.RESET_ALL + 
              Fore.GREEN + project_path + Style.RESET_ALL)
        print(Style.BRIGHT + "Programming Language: " + Style.RESET_ALL + 
              Fore.GREEN + programming_language + Style.RESET_ALL)

        # Validate supported languages
        if programming_language in ["JAVA", "PYTHON"]:
            execute_processing(project_path, programming_language)
        else:
            print(Fore.RED + Style.BRIGHT + 
                  "Execution failed - Unsupported language: " + 
                  programming_language + Style.RESET_ALL)
    else:
        print(Fore.RED + Style.BRIGHT + 
              "Execution failed - Required arguments: project_dir | code_language" + 
              Style.RESET_ALL)
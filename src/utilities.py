# ---------------------------------------------------------
# Script: Project Analysis Utilities
# Developer: Shaker Mahmud Khandaker
# Project: AugmenTest
# Last Updated: March 18, 2025
# Purpose: Provides core utilities for test execution and 
#          project structure analysis, including class
#          metadata extraction and test suite processing.
# ---------------------------------------------------------

import os
import shutil
import json
import subprocess
from colorama import Fore, init
from config import *
from test_runner import TestRunner
from java_parser import JavaClassParser


class ProjectUtilities:

    @staticmethod
    def execute_test_suite(test_path, target_path, test_filename, package, class_name): 
        test_executor = TestExecutor(test_path, target_path, test_filename, package, class_name)
        return test_executor.run_test_suite()

    @staticmethod
    def analyze_project(target_path, code_language):
        """
        Run parse task, extract class information of target project.
        """
        project_analyzer = ProjectAnalyzer(target_path, code_language)
        return project_analyzer.process_project(target_path) 


class TestExecutor:

    def __init__(self, test_path, target_path, test_filename, package, class_name):
        init()
        self.test_path = test_path
        self.target_path = target_path
        self.test_filename = test_filename
        self.package = package
        self.class_name = class_name
        self.runner = TestRunner(test_path, target_path, test_filename, package, class_name)

    def run_test_suite(self):
        return self.runner.compile_and_run_test()


class ProjectAnalyzer:

    def __init__(self, project_dir, lang):
        self.parser = JavaClassParser(get_grammar(lang), get_language(lang))
        self.output = project_dir + class_info_output
        self.lang = lang

    def process_project(self, target_path):
        # Create folders
        target_path = target_path.rstrip('/')

        out_dir = self.output
        # Check if the directory exists
        if os.path.exists(out_dir):
            # If it exists, delete it and its contents
            shutil.rmtree(out_dir)

        os.makedirs(out_dir, exist_ok=True)
        
        total_classes, output_path = self.process_classes(target_path)
        return output_path

    def process_classes(self, target_path): 
        if not os.path.exists(target_path):
            return 0, ""
        try:
            result = subprocess.check_output(['find', target_path, '-name', '*'+get_extension(self.lang)])
            code = result.decode('ascii').splitlines()
        except:
            return 0, ""
        
        project_name = os.path.split(target_path)[1]
        output = os.path.join(self.output, project_name)
        os.makedirs(output, exist_ok=True)
        return self.parse_classes(code, project_name, output), output

    def parse_classes(self, java_files, project_name, output):
        classes = {}
        for java_file in java_files:
            parsed_classes = self.parser.parse_file(java_file)
            for _class in parsed_classes:
                _class["project_name"] = project_name
                
            classes[java_file] = parsed_classes
            json_path = os.path.join(output, os.path.split(java_file)[1] + ".json")
            self.save_results(classes[java_file], json_path)
        return classes

    @staticmethod
    def save_results(data, out):
        """
        Exports data as json file
        """
        directory = os.path.dirname(out)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(out, "w") as text_file:
            data_json = json.dumps(data)
            text_file.write(data_json)

    def find_class_path(self, start_path, filename):
        for root, dirs, files in os.walk(start_path):
            if filename in files:
                return os.path.join(root, filename)
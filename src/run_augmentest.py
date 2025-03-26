# ---------------------------------------------------------
# Script: AugmenTest Automation Pipeline
# Developer: Shaker Mahmud Khandaker
# Project: AugmenTest
# Purpose: End-to-end test processing from project directory to oracle generation
# ---------------------------------------------------------

import os
import csv
import subprocess
import argparse
import datetime
from tools import *
from pathlib import Path
from config import *

# Constants
PREPROCESS_SCRIPT = "run_preprocess_test_cases.py"
AUGMENTEST_SCRIPT = "run_oracle_generation.py"

def run_preprocessing(project_dir, language):
    """Execute the preprocessing script"""
    cmd = [
        "python", PREPROCESS_SCRIPT,
        project_dir,
        language.lower()
    ]
    print(f"\nRunning AUGMENTEST preprocessing: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Preprocessing failed: {e}")
        return False

def process_test_cases(project_dir):
    """Process all test cases from generated CSV"""
    if not os.path.exists(augmentest_csv_input):
        print(f"Error: Input CSV not found at {augmentest_csv_input}")
        return False

    with open(augmentest_csv_input, mode='r') as csv_file:
        reader = csv.DictReader(csv_file)
        
        # Verify required columns exist
        required_columns = {'ID', 'project_dir', 'class_name', 'method_name'}
        if not required_columns.issubset(reader.fieldnames):
            missing = required_columns - set(reader.fieldnames)
            print(f"Error: CSV file missing required columns: {missing}")
            print(f"Existing columns: {reader.fieldnames}")
            return False
            
        for row in reader:
            try:
                test_id = row['ID']
                project_path = os.path.normpath(row['project_dir'])
                class_name = row['class_name']
                method_name = row['method_name']
                
                print(f"\nProcessing test case {test_id}...")
                cmd = [
                    "python", AUGMENTEST_SCRIPT,
                    test_id,
                    project_path,
                    class_name,
                    method_name,
                    DEFAULT_MODEL,
                    DEFAULT_VARIANT,
                    DEFAULT_USE_COMMENTS
                ]
                
                subprocess.run(cmd, check=True)
            except KeyError as e:
                print(f"Missing required value in row: {e}")
                continue
            except subprocess.CalledProcessError as e:
                print(f"Failed to process {test_id}: {e}")
                continue

    # Generate timestamp for processed file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name, ext = os.path.splitext(augmentest_csv_input)
    processed_csv = f"{base_name}_processed_{timestamp}{ext}"
    
    try:
        os.rename(augmentest_csv_input, processed_csv)
        print(f"\nProcessing complete. Output: {processed_csv}")
    except OSError as e:
        print(f"Error renaming file: {e}")

    return True

def main():
    parser = argparse.ArgumentParser(description='AugmenTest automation pipeline')
    parser.add_argument('project_dir', help='Path to project directory')
    parser.add_argument('language', help='Programming language (java/python)')
    
    args = parser.parse_args()

    # Verify project directory exists
    if not os.path.exists(args.project_dir):
        print(f"Error: Project directory not found at {args.project_dir}")
        return

    # Step 1: Preprocessing
    if not run_preprocessing(args.project_dir, args.language):
        return

    # Step 2: Test case processing
    process_test_cases(args.project_dir)

if __name__ == '__main__':
    main()
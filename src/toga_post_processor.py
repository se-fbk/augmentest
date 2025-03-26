import csv
import os
import pandas as pd
from run_evoOracle import run
from tools import *

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

# Base path where all run directories are located
# base_dir = '/home/shaker/git/toga/output/default/'
base_dir = '/home/shaker/git/toga/output/unfiltered/'


# Dataset CSV file path
dataset_file_path = '/home/shaker/git/EvoOracle-Paper/data/EvoOracle_Dataset_java.csv'

# Load Dataset
dataset = pd.read_csv(dataset_file_path)

# Loop through all run directories (from run_01 to run_10)
for run_number in range(1, 11):
    run_dir = os.path.join(base_dir, f'run_{run_number:02d}')  # creates paths like run_01, run_02, ..., run_10
    input_file_path = os.path.join(run_dir, 'oracle_preds.csv')
    
    if not os.path.exists(input_file_path):
        print(f"File {input_file_path} does not exist. Skipping...")
        continue
    
    # Open the input file for reading
    with open(input_file_path, 'r', newline='', encoding='utf-8') as csv_in:
        # Read the file content as a single string to handle custom delimiters
        file_content = csv_in.read()
        
        # Use a different approach to parse the CSV using the `"` as a delimiter
        reader = csv.DictReader(file_content.splitlines(), delimiter=',')
        fieldnames = reader.fieldnames
        
        if 'project' not in fieldnames or 'assert_pred' not in fieldnames:
            print(f"Error: Required column(s) not found in {input_file_path}.")
            continue
        
        # Process each row
        for row in reader:
            try:
                assertion = row['assert_pred']
                row['TestID'] = row['project'].split('_')[0]
            
                # If a non-empty assertion was found, update 'assertion_generated' to TRUE
                if assertion:
                    assertion = semicolonFormatter(assertion)
                
                df_row = dataset[dataset['TestID'] == row['TestID']]
            
                # Extract values from the dataframe row and the input row
                test_id = row['TestID']
                project_dir =  str(os.path.join(df_row['MutatedProjectDir'].values[0], 'original/'))
                
                test_class_name = df_row['TestClassName'].values[0]
                failed_tests = df_row['FailedTests'].values[0]
                model = "TOGA"
                # variant = "TOGA_DEFAULT"
                variant = "TOGA_UNFILTERED"
                used_developer_comments = True
                assertion_value = assertion

                # Call the run function with the printed values
                result = run(
                    test_id,
                    project_dir,
                    test_class_name,
                    failed_tests,
                    model,
                    variant,
                    used_developer_comments,
                    True,
                    assertion_value
                )

            except KeyError as e:
                print(f"KeyError: {e} - Skipping row")
                continue

print("TOGA post-processing completed for all runs.")

from run_evoOracle import run
import csv
import re
import pandas as pd
from tools import *

# Dataset CSV file path
dataset_file_path = '/home/shaker/git/EvoOracle-Paper/data/EvoOracle_Dataset_java.csv'
# Load Dataset
dataset = pd.read_csv(dataset_file_path)

# Input CSV file path
input_file_path = '/home/shaker/git/EvoOracle-Paper/data/all_data.csv'

# Output CSV file path
output_file_path = '/home/shaker/git/EvoOracle-Paper/data/all_data_processed.csv'

# Open the input file for reading and the output file for writing
with open(input_file_path, 'r', newline='', encoding='utf-8') as csv_in, \
     open(output_file_path, 'w', newline='', encoding='utf-8') as csv_out:
    
    # Read the file content as a single string to handle custom delimiters
    file_content = csv_in.read()
    
    # Use a different approach to parse the CSV using the `"` as a delimiter
    reader = csv.DictReader(file_content.splitlines(), delimiter=',', quotechar='"')
    fieldnames = reader.fieldnames
    
    if 'prompts_and_responses' not in fieldnames or 'assertion_generated' not in fieldnames:
        print("Error: Required column(s) not found.")
        exit(1)
    
    writer = csv.DictWriter(csv_out, fieldnames=fieldnames, delimiter=',', quotechar='"')
    
    # Write the header to the output file
    writer.writeheader()


    # Process each row
    for row in reader:
        try:
            # Check if 'assertion_generated' is FALSE
            if row['assertion_generated'].strip().upper() == 'FALSE':
                # Extract assertion statement from 'prompts_and_responses' column
                prompts_and_responses = row['prompts_and_responses']
                assertion = extract_complex_assertion(prompts_and_responses)
                
                # If a non-empty assertion was found, update 'assertion_generated' to TRUE
                if assertion:
                    assertion = semicolonFormatter(assertion)
                    row['assertion_generated'] = 'TRUE'
                else:
                    assertion = extract_simple_assertion(prompts_and_responses)
                    if assertion:
                        assertion = semicolonFormatter(assertion)
                        row['assertion_generated'] = 'TRUE'

                if assertion:
                    df_row = dataset[dataset['TestID'] == row['test_id']]
                
                    # Extract values from the dataframe row and the input row
                    test_id = row['test_id']
                    project_dir = row['project_dir']
                    test_class_name = df_row['TestClassName'].values[0]
                    failed_tests = df_row['FailedTests'].values[0]
                    model = row['model']
                    variant = row['variant']
                    used_developer_comments = row['used_developer_comments']
                    assertion_value = assertion

                    # Print the values of the variables
                    # print(f"TestID: {test_id}")
                    # print(f"Project Directory: {project_dir}")
                    # print(f"Test Class Name: {test_class_name}")
                    # print(f"Failed Tests: {failed_tests}")
                    # print(f"Model: {model}")
                    # print(f"Variant: {variant}")
                    # print(f"Used Developer Comments: {used_developer_comments}")
                    # print(f"Assertion: {assertion_value}")

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

                    # print("TOOL RESPONSE : ", str(result))

                    # Update row based on post-processing
                    row['eo_assertions'] = assertion
                    row['eo_compiled_original'] = result['eo_compiled_original']
                    row['eo_run_original'] = result['eo_run_original']
                    row['eo_test_path_original'] = result['eo_test_path_original']
                    
                    row['eo_compiled_buggy'] = result['eo_compiled_buggy']
                    row['eo_run_buggy'] = result['eo_run_buggy']
                    row['eo_test_path_buggy'] = result['eo_test_path_buggy']
                    	
                    attempts = int(row['attempts'])
                    incremented_value = attempts + 1
                    row['attempts'] = incremented_value

                    row['eo_assertions'] = assertion
                
            # Write the (possibly updated) row to the output file
            writer.writerow(row)
        
        except KeyError as e:
            print(f"KeyError: {e} - Skipping row")
            continue

print(f'Assertion extraction completed. Output saved to {output_file_path}')

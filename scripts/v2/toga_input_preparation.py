import pandas as pd
import json
import os
import re

# Load the CSV files
csv1 = pd.read_csv('/home/shaker/Desktop/temp/EvoOracle_Dataset.csv')
csv2 = pd.read_csv('/home/shaker/Desktop/temp/EvoOracle_Experiment_Data.csv')

# Extract TestID from CSV2's test_id column
csv2['TestID'] = csv2['test_id'].apply(lambda x: x.split('_')[0])

# Drop duplicates in CSV2 to keep only one entry per TestID
csv2_unique = csv2.drop_duplicates(subset='TestID')

# Merge CSV1 and the unique rows from CSV2 on TestID
merged_df = pd.merge(csv1, csv2_unique, on='TestID')

# Print the first 5 entries of the new table
# print(merged_df.head())
# print("Count of entries in the merged table:", len(merged_df))
# print(merged_df.columns)

# Initialize lists to store data for input.csv and meta.csv
input_data = []
meta_data = []

# Define the regular expression for focal_method_name
regex = r'\b(assert(?:True|False|Null|NotNull|Equals|NotEquals|Same|NotSame|ArrayEquals|That)?|fail|verifyException)\b[^;]*'

for index, row in merged_df.iterrows():
    # Load JSON file
    json_file_path = os.path.join(row['MutatedProjectDir'], 'original', 'output_resources', 'db.json')
    with open(json_file_path, 'r') as f:
        json_data = json.load(f)

    # Get the test class and test case names from merged_df
    test_class = row['TestClassName']
    test_case_name = row['FailedTests']
    
    # Find the test class JSON entry
    test_class_json_entry = next((entry for entry in json_data if entry['class_name'] == test_class), None)
    if not test_class_json_entry:
        print("TEST CLASS NOT FOUND : ", test_class)
        continue
    
    # Find the test case JSON entry
    test_case_json_entry = next((entry for entry in test_class_json_entry['methods'] if entry['method_name'] == test_case_name), None)
    if not test_case_json_entry:
        print("TEST CASE NOT FOUND : ", test_case_name)
        continue
    
    # Get the test package
    test_package = test_class_json_entry['package']
    if test_package.startswith("package "):
        test_package = test_package[len("package "):]
    if test_package.endswith(";"):
        test_package = test_package[:-1]

    # Find the focal method name
    focal_method_name = ''
    # for method in reversed(test_case_json_entry['focal_methods']):
    #     if not re.match(regex, method):
    #         focal_method_name = method
    #         break
    try:
        method_string = row['Method']

        # Split with '@' and get the second part
        method_part = method_string.split('@')[1]

        # Extract the string name before the parenthesis
        focal_method_name = method_part.split('(')[0]

    except IndexError:
        # Handle the case where '@' is not present or there's an issue with the split operation
        focal_method_name = ''

    except Exception as e:
        # Handle any other unexpected exceptions
        focal_method_name = ''
    
    # print(focal_method_name)

    # If focal_method_name contains a dot, split and take the second part
    if '.' in focal_method_name:
        focal_method_name = focal_method_name.split('.')[-1]

    # Get the focal class name
    focal_class = row['ClassName']
    
    # Find the focal class JSON entry
    focal_class_json_entry = next((entry for entry in json_data if entry['class_name'] == focal_class), None)
    if not focal_class_json_entry:
        print("FOCAL CLASS NOT FOUND : ", focal_class)
        continue
    
    focal_method = ''
    docstring = ''
    
    # Find the focal method JSON entry
    focal_method_json_entry = next((entry for entry in focal_class_json_entry['methods'] if entry['method_name'] == focal_method_name), None)
    if not focal_method_json_entry:
        print("TESTID : ", row['TestID'], " -   FM not found : ", focal_method_name)
        # continue
    else:
    # Get data for input.csv
        focal_method = focal_method_json_entry['source_code']
        docstring = focal_method_json_entry['dev_comments']
    
    test_prefix = test_case_json_entry['source_code']
    input_data.append([focal_method, test_prefix, docstring])
    
    # Get data for meta.csv
    project = row['TestID'] + "_" + row['FinalProject']
    bug_num = 5
    test_name = f"{test_package}.{test_class}::{test_case_name}"
    exception_bug = 0
    assertion_bug = 0
    exception_lbl = "True" if row['es_assertions'].startswith("fail") else "False"
    assertion_lbl = "" if row['es_assertions'].startswith("fail") else row['es_assertions']
    assert_err = ""
    meta_data.append([project, bug_num, test_name, exception_bug, assertion_bug, exception_lbl, assertion_lbl, assert_err])

# Convert data to DataFrame and save to CSV files
input_df = pd.DataFrame(input_data, columns=['focal_method', 'test_prefix', 'docstring'])
input_df.to_csv('toga/input.csv', index=False)

meta_df = pd.DataFrame(meta_data, columns=['project', 'bug_num', 'test_name', 'exception_bug', 'assertion_bug', 'exception_lbl', 'assertion_lbl', 'assert_err'])
meta_df.to_csv('toga/meta.csv', index=False)




print("Count of entries in the merged table:", len(merged_df))
# print(merged_df.columns)

print("Count of entries in the input_df table:", len(input_df))
# print(input_df.columns)

print("Count of entries in the meta_df table:", len(meta_df))
# print(meta_df.columns)

#!/bin/bash

# Set the path to the parent directory
PARENT_DIR="/home/shaker/Desktop/mutants_io/mutated_projects"

# Set the output CSV file
OUTPUT_CSV="/home/shaker/Desktop/mutants_io/original_list_project_info_commands.csv"

# Write the header to the CSV file
# echo "command" > $OUTPUT_CSV

# Loop through each project folder in the parent directory
for project_dir in "$PARENT_DIR"/*; do
    if [ -d "$project_dir" ]; then
        # Get the base name of the project directory
        project_name=$(basename "$project_dir")
        
        # Construct the command
        command="python run_test_case_list_gen.py $PARENT_DIR/$project_name/original/ java"
        
        # Append the command to the CSV file
        echo "$command" >> $OUTPUT_CSV
    fi
done

echo "CSV file '$OUTPUT_CSV' has been created."

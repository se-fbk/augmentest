#!/bin/bash

# Set the path to the parent directory
PARENT_DIR="/home/shaker/Documents/oracle_paper_v2/projects/flaky_java_projects"

# Set the base path for output CSV files
OUTPUT_BASE="/home/shaker/Desktop/mutants_io/merged_db/filtered_merged_db"

# Set the maximum number of entries per CSV file
MAX_ENTRIES_PER_CSV=100000

# Write the header to the first output CSV file
HEADER="project_name,project_dir,class_name,class_path,method_name,dev_comments"

# Initialize counters
entry_count=0
file_count=1

# Create the first output CSV file and write the header
OUTPUT_CSV="${OUTPUT_BASE}_$(printf "%02d" $file_count).csv"
echo "$HEADER" > "$OUTPUT_CSV"

# Loop through each project folder in the parent directory
for project_dir in "$PARENT_DIR"/*; do
    if [ -d "$project_dir" ]; then
        # Construct the path to the db.csv file
        db_csv="$project_dir/output_resources/db.csv"
        
        if [ -f "$db_csv" ]; then
            # Read the file line by line, skipping the header
            tail -n +2 "$db_csv" | while IFS= read -r line; do
                # Check if we've reached the maximum number of entries for the current CSV file
                if [ $entry_count -ge $MAX_ENTRIES_PER_CSV ]; then
                    # Reset the entry count and increment the file count
                    entry_count=0
                    ((file_count++))
                    # Create a new CSV file and write the header
                    OUTPUT_CSV="${OUTPUT_BASE}_$(printf "%02d" $file_count).csv"
                    echo "$HEADER" > "$OUTPUT_CSV"
                fi
                # Append the line to the current output CSV file
                echo "$line" >> "$OUTPUT_CSV"
                # Increment the entry count
                ((entry_count++))
            done
        else
            echo "Warning: $db_csv does not exist."
        fi
    fi
done

echo "CSV files have been created."

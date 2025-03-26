import os
import json

def process_json_files_in_directory(base_directory):
    # Iterate through all items in the base directory
    for project_folder in os.listdir(base_directory):
        project_dir = os.path.join(base_directory, project_folder)
        
        # Define the paths for input and output JSON files
        input_json_path = os.path.join(project_dir, "original/output_resources/db.json")
        output_json_path = os.path.join(project_dir, "original/output_resources/db_rag.json")
        
        # Check if the input JSON file exists
        if os.path.isfile(input_json_path):
            # Load JSON data from the file
            with open(input_json_path, 'r') as file:
                json_data = json.load(file)
            
            # Key to remove
            key_to_remove_01 = 'source_code'
            key_to_remove_02 = 'source_code_with_placeholder'

            # Filter and modify the JSON data
            filtered_json_data = []

            for item in json_data:
                # Skip items where "contains_test" is true
                if item.get("contains_test", False):
                    continue
                
                if key_to_remove_01 in item:
                    del item[key_to_remove_01]
                if key_to_remove_02 in item:
                    del item[key_to_remove_02]

                # Remove the key within the 'methods' list if it exists
                for method in item.get("methods", []):
                    if key_to_remove_01 in method:
                        del method[key_to_remove_01]
                    if key_to_remove_02 in method:
                        del method[key_to_remove_02]

                # Add the filtered item to the new list
                filtered_json_data.append(item)

            # Save the modified JSON back to the file
            with open(output_json_path, 'w') as file:
                json.dump(filtered_json_data, file, indent=4)

            # print success message
            print(f"Processed {input_json_path} and saved to {output_json_path}")

# Specify the base directory containing all the project folders
base_directory = '/home/shaker/Desktop/mutants_io/mutated_projects'

# Call the function
process_json_files_in_directory(base_directory)
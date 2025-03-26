import os
import json
from openai import OpenAI
from config import *

def process_project_folders(base_directory, output_json_path):
    client = OpenAI(api_key=openai_api_key)
    project_vector_ids = {}

    # Iterate through all items in the base directory
    for project_folder in os.listdir(base_directory):
        project_dir = os.path.join(base_directory, project_folder)
        
        # Define the path to the modified JSON file
        json_file_path = os.path.join(project_dir, "original/output_resources/db_rag.json")
        
        # Check if the JSON file exists
        if os.path.isfile(json_file_path):
            # Create a vector store with the project name
            vector_store = client.beta.vector_stores.create(name=project_folder)
            
            # Ready the file for upload to OpenAI
            with open(json_file_path, "rb") as file_stream:
                # Use the upload and poll SDK helper to upload the file, add it to the vector store,
                # and poll the status of the file batch for completion.
                file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store.id, files=[file_stream]
                )
            
            # Save the vector store ID with the project name in a dictionary
            project_vector_ids[project_folder] = vector_store.id
            
            # Print the status and file counts to see the result of this operation
            print(f"Processed {json_file_path} for project {project_folder}")
            print("Batch Status:", file_batch.status)
            print("File Counts:", file_batch.file_counts)
            print("Vector Store ID:", vector_store.id)
            print()
            print()
    
    # Save the project names and their corresponding vector store IDs to the output JSON file
    with open(output_json_path, 'w') as output_file:
        json.dump(project_vector_ids, output_file, indent=4)
    print(f"Saved vector store IDs to {output_json_path}")

# Specify the base directory containing all the project folders
base_directory = '/home/shaker/Desktop/mutants_io/mutated_projects'
# base_directory = '/home/shaker/Desktop/mutants_io/temp'

# Specify the output JSON file path
output_json_path = '/home/shaker/Desktop/mutants_io/evo_out/rag_vector_store_ids.json'

# Call the function
process_project_folders(base_directory, output_json_path)

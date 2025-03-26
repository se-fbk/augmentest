import csv

# Function to generate commands
def generate_commands_from_csv(csv_file):
    commands = []
    
    # Open the CSV file
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        
        # Iterate over each row in the CSV
        for row in reader:
            # Extract required fields
            run = row['Run']
            mutated_project_dir = row['MutatedProjectDir']
            test_class_name = row['TestClassName']
            failed_tests = row['FailedTests']
            
            # Generate the command
            command = f"python run_evoOracle.py {run} {mutated_project_dir}/original/ {test_class_name} {failed_tests} gpt-4o_openai LLM true"
            commands.append(command)
    
    return commands

# Main function to write the commands to a text file
def main(csv_file, output_file):
    commands = generate_commands_from_csv(csv_file)
    
    # Write the commands to a text file
    with open(output_file, mode='w') as file:
        for command in commands:
            file.write(command + '\n')

# Example usage
if __name__ == "__main__":
    input_csv = '/home/shaker/Desktop/mutants_io/EvoOracle_Dataset.csv'  # Replace with your CSV file path
    output_txt = '/home/shaker/Desktop/mutants_io/evo_out/EvoOracle_Dataset_commands_output.txt'  # Output file where commands will be written
    main(input_csv, output_txt)

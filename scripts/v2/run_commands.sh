#!/bin/bash

# Change to the evooracle directory
cd /home/shaker/git/evooracle

# Activate the Python virtual environment
source evooracle_venv_02/bin/activate

# Change to the src directory
cd /home/shaker/git/evooracle/src

# Path to the TXT file
csv_file="/home/shaker/Desktop/mutants_io/evo_out/EvoOracle_Dataset_commands_output.txt"

# Read and execute each command from the TXT file
while IFS= read -r command; do
    echo "Executing: $command"
    eval "$command"
done < "$csv_file"

# Deactivate the virtual environment after execution
deactivate

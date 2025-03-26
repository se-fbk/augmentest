#!/bin/bash

# Specify the directory where the folders are located
TARGET_DIR="/home/shaker/Desktop/mutants_io/run_001/mutated_projects"

# Loop through each item in the target directory
for ITEM in "$TARGET_DIR"/*; do
    # Check if the item is a directory
    if [ -d "$ITEM" ]; then
        # Get the basename of the directory
        BASENAME=$(basename "$ITEM")
        # Construct the new name with "B_" prefix
        NEWNAME="A_$BASENAME"
        # Rename the directory
        mv "$ITEM" "$TARGET_DIR/$NEWNAME"
    fi
done

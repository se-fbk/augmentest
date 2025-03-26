#!/bin/bash

# Check if directory argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

# Directory containing projects
PROJECTS_DIR="$1"

# Loop through each project in the main directory
for PROJECT_DIR in "$PROJECTS_DIR"/*; do
  if [ -d "$PROJECT_DIR" ]; then
    echo "Processing project: $PROJECT_DIR"

    # Loop through the 'original' and 'buggy' subdirectories
    for VERSION_DIR in "$PROJECT_DIR"/{original,buggy}; do
      if [ -d "$VERSION_DIR" ]; then
        echo "  Processing version: $VERSION_DIR"
        
        # Navigate to the version directory
        cd "$VERSION_DIR" || { echo "Failed to navigate to $VERSION_DIR"; continue; }

        # Run Maven compile
        mvn compile
        if [ $? -ne 0 ]; then
          echo "  Maven compile failed for $VERSION_DIR"
          continue
        fi

        # Run Maven copy-dependencies
        mvn dependency:copy-dependencies
        if [ $? -ne 0 ]; then
          echo "  Maven dependency copy failed for $VERSION_DIR"
          continue
        fi

        echo "  Finished processing $VERSION_DIR"
      else
        echo "  Skipping non-existent directory: $VERSION_DIR"
      fi
    done

    echo "Finished processing project: $PROJECT_DIR"
  fi
done

echo "All projects processed."

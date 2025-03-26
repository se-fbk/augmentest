#!/bin/bash

# set -e

MAX_ENTRIES=700
MAX_MUTANTS_ATTEMPT=5
MAJOR_HOME="/home/shaker/Programs/major/"
BASE_PATH="/home/shaker/Desktop/mutants_io"
# INPUT_CSV="$BASE_PATH/db.csv"
# INPUT_CSV="/home/shaker/Desktop/mutants_io/merged_db/db.csv"
INPUT_CSV="/home/shaker/Desktop/mutants_io/merged_db/randomized_db_filtered.csv"
TARGET_DIR="$BASE_PATH/mutated_projects"
TEMP_DIR="$BASE_PATH/temp"
TEMP_PROJECTS_DIR="$BASE_PATH/temp_projects"
CSV_FILE="$BASE_PATH/mutants.csv"
ADDITIONAL_JARS="/home/shaker/Documents/oracle_paper_v2/jars"
ORIGINAL="original"
BUGGY="buggy"
EVOSUITE_JAR="/home/shaker/Documents/oracle_paper_v2/jars/evosuite-1.2.0.jar"
EVOSUITE_TEST="evosuite-tests"
RUN_LISTENER="/home/shaker/git/evooracle/scripts/RunListener"

# Check if the CSV file already exists; if not, initialize it with headers
if [ ! -f "$CSV_FILE" ]; then
  echo "Project,ClassName,TestClassName,MutatedProjectDir,OriginalFile,MutantFile,MutantID,MutationOperator,OriginalOperator,ReplacementOperator,Method,LineNumber,Transformation,TestStatus,FailedTests,Timestamp,cmd_org,cmd_bug" > "$CSV_FILE"
fi

if [ ! -d "$TEMP_DIR" ]; then
  mkdir -p "$TEMP_DIR"
fi

if [ ! -d "$TEMP_PROJECTS_DIR" ]; then
  mkdir -p "$TEMP_PROJECTS_DIR"
fi

# Skip the header line and read the CSV file
tail -n +2 "$INPUT_CSV" | while IFS=',' read -r project_name project_dir class_name class_path method_name dev_comments; do
  if [ -d "$project_dir" ]; then
    PROJECT_NAME="$project_name"
    PROJECT_PATH=$(echo "$project_dir" | sed 's:/*$::')  # Remove trailing slashes
    JAVA_FILE="$class_path"

    TEMP_CLASS_FOLDER="$PROJECT_NAME.$class_name"
    # Check if the folder exists
    if [ ! -d "$TEMP_DIR/$TEMP_CLASS_FOLDER" ]; then
      # Folder does not exist, create it, Class was not processed.
      mkdir -p "$TEMP_DIR/$TEMP_CLASS_FOLDER"

      # Construct the classpath including JARs from both dependency and additional JARs directories
      if [ ! -d "$PROJECT_PATH/target/dependency" ]; then
        CP="$PROJECT_PATH/target/classes"
      else
        CP=$(find "$PROJECT_PATH/target/dependency" -name '*.jar' | tr '\n' ':')"$PROJECT_PATH/target/classes"
      fi

      ADDITIONAL_JARS_CP=$(find "$ADDITIONAL_JARS" -name '*.jar' | tr '\n' ':')

      # Combine classpath
      CP="$CP:$ADDITIONAL_JARS_CP"

      # echo "CP: "$CP

      # Run Major mutation plugin for the specified Java file
      $MAJOR_HOME/bin/major -cp "$CP" --mml "$MAJOR_HOME/mml/all.mml.bin" --export export.mutants "$JAVA_FILE"

      # Process the generated mutants
      MUTANTS_DIR="mutants"
      if [ -d "$MUTANTS_DIR" ]; then
        # List all subfolders in TARGET_DIR
        subfolders=("$MUTANTS_DIR"/*/)

        # Count the number of subfolders
        folder_count=${#subfolders[@]}

        # Check if the number of subfolders exceeds MAX_MUTANTS_ATTEMPT
        if [ "$folder_count" -gt "$MAX_MUTANTS_ATTEMPT" ]; then
          # Calculate how many folders to delete
          excess_count=$((folder_count - MAX_MUTANTS_ATTEMPT))

          echo "More than $MAX_MUTANTS_ATTEMPT mutants found. Deleting $excess_count excess mutants."

          # Randomly select folders to delete
          to_delete=($(shuf -e "${subfolders[@]}" -n "$excess_count"))

          for folder in "${to_delete[@]}"; do
            echo "Deleting mutant: $folder"
            rm -rf "$folder"
          done
        else
          echo "The number of mutants does not exceed the maximum limit."
        fi

        for MUTANT in "$MUTANTS_DIR"/*; do
          if [ -d "$MUTANT" ]; then
            MUTANT_ID=$(basename "$MUTANT")
            DUPLICATE_PROJECT_ORIGINAL="$TEMP_PROJECTS_DIR/${PROJECT_NAME}/${MUTANT_ID}/$ORIGINAL"
            DUPLICATE_PROJECT_BUGGY="$TEMP_PROJECTS_DIR/${PROJECT_NAME}/${MUTANT_ID}/$BUGGY"
            mkdir -p "$DUPLICATE_PROJECT_ORIGINAL"
            mkdir -p "$DUPLICATE_PROJECT_BUGGY"
            cp -r "$PROJECT_PATH/"* "$DUPLICATE_PROJECT_ORIGINAL/"
            cp -r "$PROJECT_PATH/"* "$DUPLICATE_PROJECT_BUGGY/"

            rm -rf "$DUPLICATE_PROJECT_ORIGINAL/$EVOSUITE_TEST"
            rm -rf "$DUPLICATE_PROJECT_BUGGY/$EVOSUITE_TEST"
            
            # Copy mutant files and log details
            MUTANT_FILE=$(find "$MUTANT" -name "$(basename "$JAVA_FILE")")
            if [ -n "$MUTANT_FILE" ]; then
              TARGET_MUTANT_FILE="$DUPLICATE_PROJECT_BUGGY/${JAVA_FILE#$PROJECT_PATH/}"
              cp "$MUTANT_FILE" "$TARGET_MUTANT_FILE"
              
              # Change to the buggy project directory
              current_dir=$(pwd)
              MUTANTS_LOG="$(pwd)/mutants.log"
              cd "$DUPLICATE_PROJECT_BUGGY"
              
              # Compile the project
              # set +e  # Temporarily disable exit on error
              mvn compile
              if [ $? -ne 0 ]; then
                echo "Compilation error in $DUPLICATE_PROJECT_BUGGY. Skipping mutant $MUTANT_ID."
                rm -rf "$TEMP_PROJECTS_DIR/${PROJECT_NAME}/${MUTANT_ID}"
                cd "$current_dir"
                continue
              fi
              # set -e  # Re-enable exit on error

              # Extract package name and class name
              PACKAGE_NAME=$(dirname "${JAVA_FILE#*/src/main/java/}" | tr '/' '.')
              CLASS_NAME=$(basename "$JAVA_FILE" .java)
              FULL_CLASS_NAME="$PACKAGE_NAME.$CLASS_NAME"

              TEST_CLASS_NAME=$(basename "$JAVA_FILE" .java)"_ESTest"
              FULL_TEST_CLASS_NAME="$PACKAGE_NAME.$TEST_CLASS_NAME"

              # Run EvoSuite to generate tests
              java -jar "$EVOSUITE_JAR" -class "$FULL_CLASS_NAME" -projectCP target/classes -criterion branch

              # Construct the classpath including JARs from both dependency and additional JARs directories
              if [ ! -d "target/dependency" ]; then
                CP2="target/classes"
              else
                CP2=$(find "target/dependency" -name '*.jar' | tr '\n' ':')"target/classes"
              fi
              
              # Combine classpath
              CP2="$CP2:$ADDITIONAL_JARS_CP:evosuite-tests:"
              
              # Compile the generated EvoSuite tests
              javac -cp "$CP2" evosuite-tests/$(echo "$PACKAGE_NAME" | tr '.' '/')/*.java

              CMD_bug="java -cp "$CP2" org.junit.runner.JUnitCore "$FULL_TEST_CLASS_NAME

              # Return to the original directory
              cd "$current_dir"

              # Copy the generated tests to the original project directory
              cp -r "$DUPLICATE_PROJECT_BUGGY/evosuite-tests" "$DUPLICATE_PROJECT_ORIGINAL/"

              # Change to the original project directory
              cd "$DUPLICATE_PROJECT_ORIGINAL"

              # Compile the project with the copied tests
              mvn compile
              mvn dependency:copy-dependencies

              # Construct the classpath including JARs from both dependency and additional JARs directories
              if [ ! -d "target/dependency" ]; then
                CP3="target/classes"
              else
                CP3=$(find "target/dependency" -name '*.jar' | tr '\n' ':')"target/classes"
              fi
              
              # Combine classpath
              CP3="$CP3:$ADDITIONAL_JARS_CP:$RUN_LISTENER:evosuite-tests:"

              # Compile the generated EvoSuite tests
              javac -cp "$CP3" evosuite-tests/$(echo "$PACKAGE_NAME" | tr '.' '/')/*.java

              # Run the tests
              # java -cp "$CP3" org.junit.runner.JUnitCore "$FULL_CLASS_NAME"_ESTest

              # Run the tests and capture the output
              # TEST_OUTPUT=$(java -cp "$CP3" org.junit.runner.JUnitCore "$FULL_CLASS_NAME"_ESTest | tee /dev/tty)
              # Run the tests with the custom RunListener
              TEST_OUTPUT=$(java -cp "$CP3" CustomJUnitRunner "$FULL_TEST_CLASS_NAME" | tee /dev/tty)
              echo "TEST_OUTPUT : "$TEST_OUTPUT

              # Check for test failures
              if echo "$TEST_OUTPUT" | grep -q "FAILURE"; then
                # Extract failed test cases
                FAILED_TESTS=$(echo "$TEST_OUTPUT" | awk '/##TEST_FAILURE_START##/,/##TEST_FAILURE_END##/ { if ($0 !~ /##TEST_FAILURE_(START|END)##/) print $0 }')
                
                # Print or process the failed test cases
                echo "Failed test cases:"
                echo "$FAILED_TESTS"
                TEST_STATUS="FAILED"

                MUTATED_PROJECT_PATH="$TARGET_DIR/$PROJECT_NAME.$CLASS_NAME"
                mkdir -p $MUTATED_PROJECT_PATH

                MUTATED_PROJECT_ORIGINAL="$MUTATED_PROJECT_PATH/$ORIGINAL"
                MUTATED_PROJECT_BUGGY="$MUTATED_PROJECT_PATH/$BUGGY"

                mkdir -p "$MUTATED_PROJECT_ORIGINAL"
                mkdir -p "$MUTATED_PROJECT_BUGGY"

                cp -r "$DUPLICATE_PROJECT_ORIGINAL/"* "$MUTATED_PROJECT_ORIGINAL/"
                cp -r "$DUPLICATE_PROJECT_BUGGY/"* "$MUTATED_PROJECT_BUGGY/"
                
                # Log the test results
                # Extract mutation details from mutants.log
                if [ -f "$MUTANTS_LOG" ]; then
                  while IFS=':' read -r ID OPERATOR ORIG_OP REPLACEMENT_OP METHOD LINE TRANSFORMATION; do
                    if [ "$ID" = "$MUTANT_ID" ]; then
                      TIMESTAMP=$(date +"%H:%M:%S")
                      CMD_org="java -cp "$CP3" org.junit.runner.JUnitCore "$FULL_TEST_CLASS_NAME
                      # Function to escape double quotes in a string
                      escape_quotes() {
                          echo "$1" | sed 's/"/""/g'
                      }

                      # Ensure all fields are enclosed in double quotes and internal quotes are escaped
                      TIMESTAMP=$(date +"%H:%M:%S")
                      for word in $FAILED_TESTS; do
                        # echo "Project,ClassName,TestClassName,MutatedProjectDir,OriginalFile,MutantFile,MutantID,MutationOperator,OriginalOperator,ReplacementOperator,Method,LineNumber,Transformation,TestStatus,FailedTests,Timestamp,cmd_org,cmd_bug" > "$CSV_FILE"
                        echo \"$(escape_quotes "$PROJECT_NAME")\",\"$(escape_quotes "$CLASS_NAME")\",\"$(escape_quotes "$TEST_CLASS_NAME")\",\"$(escape_quotes "$MUTATED_PROJECT_PATH")\",\"$(escape_quotes "$JAVA_FILE")\",\"$(escape_quotes "$TARGET_MUTANT_FILE")\",\"$(escape_quotes "$ID")\",\"$(escape_quotes "$OPERATOR")\",\"$(escape_quotes "$ORIG_OP")\",\"$(escape_quotes "$REPLACEMENT_OP")\",\"$(escape_quotes "$METHOD")\",\"$(escape_quotes "$LINE")\",\"$(escape_quotes "$TRANSFORMATION")\",\"$(escape_quotes "$TEST_STATUS")\",\"$(escape_quotes "$word")\","\"$(escape_quotes "$TIMESTAMP")\",\"$(escape_quotes "$CMD_org")\",\"$(escape_quotes "$CMD_bug")\"" >> "$CSV_FILE"
                      done
                      # Check the number of folders in the TARGET_DIR
                      FOLDER_COUNT=$(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)

                      if [ "$FOLDER_COUNT" -ge "$MAX_ENTRIES" ]; then
                        echo "Maximum number of entries ($MAX_ENTRIES) reached. Stopping processing."
                        exit 0
                      fi

                      break
                    fi
                  done < "$MUTANTS_LOG"
                fi
                # Return to the original directory
                cd "$current_dir"
                break
              else
                FAILED_TESTS=""
                TEST_STATUS="PASSED"
              fi

              # Return to the original directory
              cd "$current_dir"
            fi
          fi
          rm -rf "$TEMP_PROJECTS_DIR/${PROJECT_NAME}/${MUTANT_ID}"
        done
        rm -rf "$MUTANTS_DIR"
      fi
    else
      # Folder exists, skipping as class already processed
      echo "Class already processed: $class_name"
    fi    
  fi
done

# rm -rf "$TEMP_DIR"
# rm -rf "$TEMP_PROJECTS_DIR"
echo "Mutation generation finished."

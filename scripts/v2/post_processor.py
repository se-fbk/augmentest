import csv
import re

# Function to extract assertion statements
# def extract_assertion(statement):
#     # Regex pattern to match various assertion statements ending with a semicolon
#     assertion_pattern = r'(assert\w*\(.*?\);|fail\(.*?\);)'
    
#     # Find all assertion statements in the string
#     assertions = re.findall(assertion_pattern, statement)
    
#     # Return the first assertion found, or an empty string if none found
#     return assertions[0] if assertions else ''

# def extract_assertion(statement):
#     # Updated regex pattern to be case-insensitive and allow spaces
#     assertion_pattern = r'(?i)(assert\w*\s*\(.*?\);|fail\s*\(.*?\);)'
    
#     # Find all assertion statements in the string
#     assertions = re.findall(assertion_pattern, statement)
    
#     # Return the first assertion found, or an empty string if none found
#     return assertions[0] if assertions else ''

def semicolonFormatter(statement):
    """
    Adds a semicolon at the end of the statement if it does not already end with one.
    
    Parameters:
    statement (str): The input string to format.
    
    Returns:
    str: The input string with a semicolon at the end if it wasn't there already.
    """
    # Strip any leading or trailing whitespace for consistency
    statement = statement.strip()
    
    # Check if the string ends with a semicolon
    if not statement.endswith(';'):
        # Append a semicolon if it does not end with one
        statement += ';'
    
    return statement

def extract_assertion(statement):
    # Define possible assertion keywords
    assertion_keywords = ["assert", "assertTrue", "assertNull", "fail", "assertFalse", "assertNotEquals", "assertEquals", "assertArrayEquals", "assertNotNull", "assertNotSame", "assertSame", "assertThat", "assertThrows"]
    
    # Iterate through the statement to find assertion keywords
    for keyword in assertion_keywords:
        keyword_lower = keyword.lower()
        start_index = 0
        
        while True:
            start_index = statement.lower().find(keyword_lower, start_index)
            if start_index == -1:
                break
            
            # Move past the keyword
            start_index += len(keyword)
            while start_index < len(statement) and statement[start_index].isspace():
                start_index += 1
            
            # Check if it is followed by an opening parenthesis
            if start_index < len(statement) and statement[start_index] == '(':
                # Track parentheses to find the matching closing parenthesis
                open_parens = 1
                end_index = start_index + 1
                
                while end_index < len(statement) and open_parens > 0:
                    if statement[end_index] == '(':
                        open_parens += 1
                    elif statement[end_index] == ')':
                        open_parens -= 1
                    end_index += 1
                
                # Check for a trailing semicolon
                if end_index < len(statement) and statement[end_index] == ';':
                    end_index += 1
                
                # Extract and return the assertion statement
                return statement[start_index - len(keyword):end_index].strip()
            
            # Move to the next occurrence
            start_index += len(keyword)
    
    return ''

def extract_simple_assertion(statement):
    """
    Extracts simple assertion statements such as 'assert true;', 'assert false', and 'assert false;'
    from within a larger text block.
    
    Parameters:
    statement (str): The input string to extract assertion from.
    
    Returns:
    str: The extracted assertion statement, or an empty string if no assertion is found.
    """
    # Normalize the statement for consistent comparison
    statement = statement.strip()
    
    # Define the possible assertion patterns with optional semicolon
    assertion_patterns = [
        r"\bassert true\b;?",
        r"\bassert false\b;?"
    ]
    
    # Check for the patterns
    for pattern in assertion_patterns:
        # Use regex to find patterns anywhere in the statement
        match = re.search(pattern, statement)
        if match:
            # Return the match with a semicolon if it's not present
            return match.group() if match.group().endswith(';') else f"{match.group()};"
    
    # If no match found, return an empty string
    return ''



# Input CSV file path
# input_file_path = '/home/shaker/git/EvoOracle-Paper/data/row_with_empty_assertions.csv'
input_file_path = '/home/shaker/git/EvoOracle-Paper/data/all_data.csv'
# Output CSV file path
output_file_path = '/home/shaker/git/EvoOracle-Paper/data/row_with_empty_assertions_processed.csv'

# Open the input file for reading and the output file for writing
with open(input_file_path, 'r', newline='', encoding='utf-8') as csv_in, \
     open(output_file_path, 'w', newline='', encoding='utf-8') as csv_out:
    
    # Read the file content as a single string to handle custom delimiters
    file_content = csv_in.read()
    
    # Use a different approach to parse the CSV using the `"` as a delimiter
    reader = csv.DictReader(file_content.splitlines(), delimiter=',', quotechar='"')
    fieldnames = reader.fieldnames
    
    if 'prompts_and_responses' not in fieldnames or 'assertion_generated' not in fieldnames:
        print("Error: Required column(s) not found.")
        exit(1)
    
    writer = csv.DictWriter(csv_out, fieldnames=fieldnames, delimiter=',', quotechar='"')
    
    # Write the header to the output file
    writer.writeheader()
    
    # Process each row
    for row in reader:
        try:
            # Check if 'assertion_generated' is FALSE
            if row['assertion_generated'].strip().upper() == 'FALSE':
                # Extract assertion statement from 'prompts_and_responses' column
                prompts_and_responses = row['prompts_and_responses']
                assertion = extract_assertion(prompts_and_responses)
                
                # If a non-empty assertion was found, update 'assertion_generated' to TRUE
                if assertion:
                    assertion = semicolonFormatter(assertion)
                    row['assertion_generated'] = 'TRUE'
                else:
                    assertion = extract_simple_assertion(prompts_and_responses)
                    if assertion:
                        assertion = semicolonFormatter(assertion)
                        row['assertion_generated'] = 'TRUE'


                # Update 'eo_assertions' column with the extracted assertion
                row['eo_assertions'] = assertion
            
            # Write the (possibly updated) row to the output file
            writer.writerow(row)
        
        except KeyError as e:
            print(f"KeyError: {e} - Skipping row")
            continue

print(f'Assertion extraction completed. Output saved to {output_file_path}')

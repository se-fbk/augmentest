import time
import javalang
import jinja2
import os.path
import sys
import time
from open_ai_prompter import OpenAIPrompter
from open_ai_rag import OpenAIRagPrompter

from tools import *
from colorama import Fore, Style, init
from utilities import ProjectUtilities
from gpt4all import GPT4All
from variants import Variants

init()
# Create a jinja2 environment
env = jinja2.Environment(loader=jinja2.FileSystemLoader('../prompt'))

# BASE_PATH = '/home/shaker/models/GPT4All/'
BASE_PATH = LLM_BASE_PATH
# PATH = f'{BASE_PATH}{"ggml-gpt4all-l13b-snoozy.bin"}'
try:
    PATH = f'{BASE_PATH}{sys.argv[5]}'
    # Callbacks support token-wise streaming
    # callbacks = [StreamingStdOutCallbackHandler()]

    llm = sys.argv[5]
    # llm = GPT4All(model=PATH, backend="gptj", callbacks=callbacks, verbose=True, temp=temperature, n_predict=n_predict, top_p=top_p, top_k=top_k, n_batch=n_batch, repeat_penalty=repeat_penalty, repeat_last_n=repeat_last_n)

    # template = PromptTemplate(input_variables=['action'], template="""{action}""")
    # chain = LLMChain(llm=llm, prompt=template, verbose=True) 
except:
    print("LLM path missing, ignoring.")



def prompt_openLLM(messages):
    # return "failed"
    # return 'assertTrue(nodeInstaller4.getNodeVersion().equals("/node"));\n  assertFalse(nodeInstaller4.getNodeVersion().equals("/node"));\n  assertSame(nodeInstaller4.getNodeVersion().equals("/node"));'
    # Retry 5 times when error occurs
    max_try = 5
    while max_try:
        try:
            # completion = chain.run(messages)
            # return completion
            model = GPT4All(llm, model_path=BASE_PATH)
            
            print("Prompt: " + Fore.GREEN + messages, Style.RESET_ALL)
            with model.chat_session():
                # print(model.generate("quadratic formula"))
                # response = model.generate(messages)
                response = "assertNotNull(eventTypeOuter_EventTypeEnum0);"
            print("Response: " + Fore.GREEN + response, Style.RESET_ALL)
            
            return response
        except Exception as e:
            print(Fore.RED + str(e), Style.RESET_ALL)
        max_try -= 1
    return ""

def prompt_ChatGPT(messages):
    # return "failed"
    # return 'assertTrue(nodeInstaller4.getNodeVersion().equals("/node"));\n  assertFalse(nodeInstaller4.getNodeVersion().equals("/node"));\n  assertSame(nodeInstaller4.getNodeVersion().equals("/node"));'
    # Retry 5 times when error occurs
    max_try = 1
    openai_chat = OpenAIPrompter()
    while max_try:
        try:
            print("Prompt: " + Fore.GREEN + messages, Style.RESET_ALL)
            
            response = openai_chat.get_completion(messages)
            
            print("Response: " + Fore.GREEN + response.choices[0].message.content, Style.RESET_ALL)
            
            return response
        except Exception as e:
            print(Fore.RED + str(e), Style.RESET_ALL)
        max_try -= 1
    return ""

def prompt_OpenAI_RAG(messages, project_id):
    # Retry up to 7 times when an error occurs
    max_try = 7
    openai_rag = OpenAIRagPrompter()
    
    while max_try > 0:
        try:
            print("Prompt: " + Fore.GREEN + messages, Style.RESET_ALL)
            
            raw_response, response = openai_rag.get_completion(messages, project_id)
            
            if raw_response and response:
                print("Response: " + Fore.GREEN + str(response), Style.RESET_ALL)
                # print("RAW Response: " + Fore.GREEN + str(raw_response), Style.RESET_ALL)
                
                return raw_response, response
            else:
                print(Fore.RED + "Empty response. Retrying... (" + str(max_try - 1) + " attempts left)", Style.RESET_ALL)
        
        except Exception as e:
            print(Fore.RED + str(e), Style.RESET_ALL)
        
        max_try -= 1
        time.sleep(1)  # Sleep before the next retry
    
    return "", ""

def generate_prompt(template_name, context: dict):
    """
    Generate prompt via jinja2 engine
    :param template_name: the name of the prompt template
    :param context: the context to render the template
    :return:
    """
    # Load template
    template = env.get_template(template_name)
    prompt = template.render(context)

    return prompt


def load_context_file(context_file):
    if isinstance(context_file, str):
        with open(context_file, "r") as f:
            return json.load(f)
    return context_file


def generate_messages(template_name, context):
    """
    This function generates messages before asking LLM, using templates.
    :param template_name: The template name of the user template.
    :param context: The context JSON file or dict to render the template.
    :return: A list of generated messages.
    """
    message = generate_prompt(template_name, context)
    
    return message


def complete_code(code):
    """
    To complete the code
    :param code:
    :return:
    """

    # We delete the last incomplete test.
    code = code.split("@Test\n")
    code = "@Test\n".join(code[:-1]) + '}'
    return code


def process_error_message(error_message, allowed_tokens):
    """
    Process the error message
    :param error_message:
    :param allowed_tokens:
    :return:
    """
    if allowed_tokens <= 0:
        return ""
    while count_tokens(error_message) > allowed_tokens:
        if len(error_message) > 50:
            error_message = error_message[:-50]
        else:
            break
    return error_message


def if_code_is_valid(code) -> bool:
    """
    Check if the code is valid
    :param code:
    :return: True or False
    """
    if "{" not in code or "}" not in code:
        return False
    try:
        javalang.parse.parse(code)
        return True
    except Exception:
        return False


def syntactic_check(code):
    """
    Syntactic repair
    :param code:
    :return: has_syntactic_error, code
    """
    if is_syntactic_correct(code):
        return False, code
    else:
        stop_point = [";", "}", "{", " "]  # Stop point
        for idx in range(len(code) - 1, -1, -1):
            if code[idx] in stop_point:
                code = code[:idx + 1]
                break
        left_bracket = code.count("{")
        right_bracket = code.count("}")
        for idx in range(left_bracket - right_bracket):
            code += "}\n"

        if is_syntactic_correct(code):
            return True, code

        matches = list(re.finditer(r"(?<=\})[^\}]+(?=@)", code))
        if matches:
            code = code[:matches[-1].start() + 1]
            left_count = code.count("{")
            right_count = code.count("}")
            for _ in range(left_count - right_count):
                code += "\n}"
        if is_syntactic_correct(code):
            return True, code
        else:
            return True, ""


def is_syntactic_correct(code):
    """
    Check if the code is syntactically correct
    :param code:
    :return:
    """
    try:
        javalang.parse.parse(code)
        return True
    except Exception as e:
        return False


def extract_code(string):
    """
    Check if the string is valid code and extract it.
    :param string:
    :return: has_code, extracted_code, has_syntactic_error
    """
    # if the string is valid code, return True
    if is_syntactic_correct(string):
        return True, string, False

    has_code = False
    extracted_code = ""
    has_syntactic_error = False

    # Define regex pattern to match the code blocks
    pattern = r"```[java]*([\s\S]*?)```"

    # Find all matches in the text
    matches = re.findall(pattern, string)
    if matches:
        # Filter matches to only include ones that contain "@Test"
        filtered_matches = [match.strip() for match in matches if
                            "@Test" in match and "class" in match and "import" in match]
        if filtered_matches:
            for match in filtered_matches:
                has_syntactic_error, extracted_code = syntactic_check(match)
                if extracted_code != "":
                    has_code = True
                    break

    if not has_code:
        if "```java" in string:
            separate_string = string.split("```java")[1]
            if "@Test" in separate_string:
                has_syntactic_error, temp_code = syntactic_check(separate_string)
                if temp_code != "":
                    extracted_code = temp_code
                    has_code = True
        elif "```" in string:
            separate_strings = string.split("```")
            for separate_string in separate_strings:
                if "@Test" in separate_string:
                    has_syntactic_error, temp_code = syntactic_check(separate_string)
                    if temp_code != "":
                        extracted_code = temp_code
                        has_code = True
                        break
        else:  # Define boundary
            allowed = ["import", "packages", "", "@"]
            code_lines = string.split("\n")
            start, anchor, end = -1, -1, -1
            allowed_lines = [False for _ in range(len(code_lines))]
            left_brace = {x: 0 for x in range(len(code_lines))}
            right_brace = {x: 0 for x in range(len(code_lines))}
            for i, line in enumerate(code_lines):
                left_brace[i] += line.count("{")
                right_brace[i] += line.count("}")
                striped_line = line.strip()

                for allow_start in allowed:
                    if striped_line.startswith(allow_start):
                        allowed_lines[i] = True
                        break

                if re.search(r'public class .*Test', line) and anchor == -1:
                    anchor = i

            if anchor != -1:
                start = anchor
                while start:
                    if allowed_lines[start]:
                        start -= 1

                end = anchor
                left_sum, right_sum = 0, 0
                while end < len(code_lines):
                    left_sum += left_brace[end]
                    right_sum += right_brace[end]
                    if left_sum == right_sum and left_sum >= 1 and right_sum >= 1:
                        break
                    end += 1

                temp_code = "\n".join(code_lines[start:end + 1])
                has_syntactic_error, temp_code = syntactic_check(temp_code)
                if temp_code != "":
                    extracted_code = temp_code
                    has_code = True

    extracted_code = extracted_code.strip()
    return has_code, extracted_code, has_syntactic_error


def extract_and_run(evooracle_source_code, evosuite_source_code, output_path, class_name, test_num, method_name, project_name, package, original_project_dir):
    """
    Extract the code and run it
    :param project_name:
    :param test_num:
    :param method_id:
    :param class_name:
    :param input_string:
    :param output_path:
    :return:
    """
    result = {}
    evo_result = {
        "eo_compiled_original": False,
        "eo_run_original": False,
        "eo_mutation_score_original": 0,
        "eo_test_path_original": None,
        "es_compiled_original": True,
        "es_run_original": False,
        "es_mutation_score_original": 0,
        "es_test_path_original": None,
        
        "eo_compiled_buggy": False,
        "eo_run_buggy": False,
        "eo_mutation_score_buggy": 0,
        "eo_test_path_buggy": None,
        "es_compiled_buggy": True,
        "es_run_buggy": True,
        "es_mutation_score_buggy": 0,
        "es_test_path_buggy": None,
        
        "prompts_and_responses": None,
    }

    has_code, extracted_code, has_syntactic_error = extract_code(evooracle_source_code)
    if not has_code:
        return evo_result
    result["has_code"] = has_code
    result["source_code"] = extracted_code
    if package:
        result["source_code"] = repair_package(extracted_code, package)
    result["has_syntactic_error"] = has_syntactic_error
    

    # print("Project Name: " + project_name)
    # print("Class Name: " + class_name)

    renamed_class_evooracle = class_name + '_' + str(test_num) + string_tables.EVOORACLE_SIGNATURE
    renamed_class_source_code_evooracle = change_class_name(extracted_code, class_name, renamed_class_evooracle)
    
    renamed_class_evosuite = class_name + '_' + str(test_num) + string_tables.EVOSUITE_UNIT_SIGNATURE
    renamed_class_source_code_evosuite = change_class_name(evosuite_source_code, class_name, renamed_class_evosuite)
    
    # process for Original Project
    original_out_dir = os.path.dirname(output_path)
    original_evooracle_test_file_name = export_method_test_case(original_out_dir, renamed_class_evooracle, renamed_class_source_code_evooracle)
    # original_evosuite_test_file_name = export_method_test_case(original_out_dir, renamed_class_evosuite, renamed_class_source_code_evosuite)

    original_response_dir = os.path.abspath(original_out_dir)
    original_target_dir = os.path.abspath(original_project_dir)

    # process for Buggy Project
    relative_path = os.path.relpath(original_out_dir, original_project_dir)
    parent_dir = os.path.dirname(os.path.dirname(original_project_dir))
    buggy_project_dir = os.path.join(parent_dir, string_tables.BUGGY_FOLDER) + '/'
    buggy_out_dir = os.path.join(buggy_project_dir, relative_path)
    
    buggy_evooracle_test_file_name = export_method_test_case(buggy_out_dir, renamed_class_evooracle, renamed_class_source_code_evooracle)
    # buggy_evosuite_test_file_name = export_method_test_case(buggy_out_dir, renamed_class_evosuite, renamed_class_source_code_evosuite)
    
    buggy_response_dir = os.path.abspath(buggy_out_dir)
    buggy_target_dir = os.path.abspath(buggy_project_dir)


    # run test

    o_test_result_eo_c, o_test_result_eo_r, o_test_result_eo_ms = ProjectUtilities.execute_test_suite(original_response_dir, original_target_dir, original_evooracle_test_file_name, package, renamed_class_evooracle)
    # o_test_result_es_c, o_test_result_es_r, o_test_result_es_ms = ProjectUtilities.execute_test_suite(original_response_dir, original_target_dir, original_evosuite_test_file_name, package, renamed_class_evosuite)
    
    b_test_result_eo_c, b_test_result_eo_r, b_test_result_eo_ms = ProjectUtilities.execute_test_suite(buggy_response_dir, buggy_target_dir, buggy_evooracle_test_file_name, package, renamed_class_evooracle)
    # b_test_result_es_c, b_test_result_es_r, b_test_result_es_ms = ProjectUtilities.execute_test_suite(buggy_response_dir, buggy_target_dir, buggy_evosuite_test_file_name, package, renamed_class_evosuite)

    # 3. Read the result

    # Original Project results
    evo_result["eo_compiled_original"] = o_test_result_eo_c
    evo_result["eo_run_original"] = o_test_result_eo_r
    evo_result["eo_mutation_score_original"] = o_test_result_eo_ms
    evo_result["eo_test_path_original"] = original_evooracle_test_file_name

    # evo_result["es_compiled_original"] = o_test_result_es_c
    # evo_result["es_run_original"] = o_test_result_es_r
    # evo_result["es_mutation_score_original"] = o_test_result_es_ms
    # evo_result["es_test_path_original"] = original_evosuite_test_file_name
    
    # Buggy Project results
    evo_result["eo_compiled_buggy"] = b_test_result_eo_c
    evo_result["eo_run_buggy"] = b_test_result_eo_r
    evo_result["eo_mutation_score_buggy"] = b_test_result_eo_ms
    evo_result["eo_test_path_buggy"] = buggy_evooracle_test_file_name

    # evo_result["es_compiled_buggy"] = b_test_result_es_c
    # evo_result["es_run_buggy"] = b_test_result_es_r
    # evo_result["es_mutation_score_buggy"] = b_test_result_es_ms
    # evo_result["es_test_path_buggy"] = buggy_evosuite_test_file_name

    return evo_result

def generate_oracle_with_LLM(project_dir, context, test_id, llm_name, variant, consider_dev_comments, fix_run, fix_assertion):
    """
    start_generation
    :param project_dir:
    :param context:
    :param test_id:
    :return:
    """

    project_name = context.get("project_name")
    test_class_name = context.get("test_class_name")
    test_class_path = context.get("test_class_path")
    
    steps, rounds = 0, 0
    
    # Get the current time in milliseconds
    start_time = time.perf_counter()
    
    result = {
        "attempts": 0, 
        "assertion_generated": False,
        "assertion_generation_time": 0,
        "eo_assertions": None,
        
        # Original
        "eo_compiled_original": False,
        "eo_run_original": False,
        "eo_mutation_score_original": 0,
        "eo_test_path_original":None,
        "es_compiled_original": False,
        "es_run_original": False,
        "es_mutation_score_original": 0,
        "es_test_path_original":None,

        # Buggy
        "eo_compiled_buggy": False,
        "eo_run_buggy": False,
        "eo_mutation_score_buggy": 0,
        "eo_test_path_buggy":None,
        
        "es_compiled_buggy": False,
        "es_run_buggy": False,
        "es_mutation_score_buggy": 0,
        "es_test_path_buggy":None,
        
        "prompts_and_responses": None,
        "variant": None,
    }
    
    prompts_and_responses = []

    if consider_dev_comments:
        prompt_template = SP_TEMPLATE
    else:
        prompt_template = SP_TEMPLATE

    # write in file if comments exist
    # write_entries_with_comments(context)
    
    # sys.exit()

    if not consider_dev_comments:
        context["focal_method_details"] = remove_key_value_pair_from_json(context.get("focal_method_details"), "developer_comments")

        # print("AFTER REMOVING DEV COMMENTS:")
        # print(context["focal_method_details"])
    
    try:
        while rounds < max_attempts:
            # 1. Prompt LLM
            steps += 1
            rounds += 1

            if variant == Variants.SIMPLE_PROMPT:
                prompt_template = SP_TEMPLATE
                messages = generate_messages(prompt_template, context)
            elif variant == Variants.EXTENDED_PROMPT:
                all_method = json.loads(context["class_method_details"])
                
                if len(all_method)>0:
                    prompt_template = EP_TEMPLATE
                else:
                    prompt_template = SP_TEMPLATE

                messages = generate_messages(prompt_template, context)
            elif variant == Variants.RAG:
                prompt_template = RAG_GEN_TEMPLATE
                messages = generate_messages(prompt_template, context)
            elif variant == Variants.SIMPLE_PROMPT_WITH_RAG:
                prompt_template = RAG_SP_TEMPLATE
                messages = generate_messages(prompt_template, context)
            elif variant == Variants.TOGA_DEFAULT:
                messages = "TOGA default"
            elif variant == Variants.TOGA_UNFILTERED:
                messages = "TOGA unfiltered"
            else:
                return "Invalid variant"
            
            # print("Prompt: " + Fore.YELLOW + messages, Style.RESET_ALL)  

            print("Attempt: " + Fore.YELLOW + str(rounds), Style.RESET_ALL)
            
            llm_raw_response = ""
            llm_extracted_response = ""
            assertions = ""
            
            if fix_run:
                llm_raw_response = fix_assertion
                llm_extracted_response = fix_assertion
                # assertions = fix_assertion
            elif variant == Variants.RAG or variant == Variants.SIMPLE_PROMPT_WITH_RAG:
                # OpenAI RAG
                project_id = os.path.basename(os.path.dirname(os.path.dirname(project_dir)))
                # print("PROJECT_ID : " + project_id)
                llm_raw_response, llm_extracted_response = prompt_OpenAI_RAG(messages, project_id)

                # assertions = llm_extracted_response
                # assertions = extract_code_block_statements(llm_extracted_response)
            elif llm_name == "gpt-4o_openai":
                # OpenAI
                llm_raw_response = prompt_ChatGPT(messages)
                # llm_extracted_response = llm_raw_response
                
                llm_extracted_response = llm_raw_response.choices[0].message.content

                # assertions = llm_extracted_response
                # assertions = extract_code_block_statements(llm_extracted_response)
            else:
                # Open LLM
                llm_raw_response = prompt_openLLM(messages)
                # assertions = extract_first_assertion_from_string(llm_raw_response)
                llm_extracted_response = llm_raw_response
                # assertions = extract_first_assertion(llm_raw_response)
            
            assertions = extract_complex_assertion(llm_extracted_response)
                
            # If a non-empty assertion was found, update 'assertion_generated' to TRUE
            if assertions:
                assertions = semicolonFormatter(assertions)
            else:
                assertions = extract_simple_assertion(prompts_and_responses)
                if assertions:
                    assertions = semicolonFormatter(assertions)
                    
            prompts_and_responses.append({"prompt":messages,"response":str(llm_raw_response), "attempt": str(rounds), "variant": variant.name})
            
            steps += 1
            
            if assertions:
                print("Assertion generation: " + Fore.GREEN + "SUCCESS", Style.RESET_ALL)
                # print("LLM Response Assertion: " + Fore.GREEN + assertions, Style.RESET_ALL)
                # print()
                
                end_time = time.perf_counter()

                print("Assertion: " + Fore.GREEN + assertions, Style.RESET_ALL)

                # evooracle_source_code = re.sub(re.escape(string_tables.ASSERTION_PLACEHOLDER), assertions, context.get("test_case_with_placeholder"))
                evooracle_source_code = context.get("test_case_with_placeholder").replace(string_tables.ASSERTION_PLACEHOLDER, assertions) 
                evosuite_source_code = context.get("evosuite_test_case")
                # print("Updated test source code:")
                # print(updated_source_code)
                
                evo_result = extract_and_run(evooracle_source_code, evosuite_source_code, test_class_path, test_class_name, test_id, context.get("method_name"),
                                                        project_name, context.get("package"), project_dir)
                
                result["assertion_generated"] = True
                result["eo_assertions"] = assertions

                # Original
                result["eo_compiled_original"] = evo_result["eo_compiled_original"]
                result["eo_run_original"] = evo_result["eo_run_original"]
                result["eo_mutation_score_original"] = evo_result["eo_mutation_score_original"]
                result["eo_test_path_original"] = evo_result["eo_test_path_original"]
                
                result["es_compiled_original"] = evo_result["es_compiled_original"]
                result["es_run_original"] = evo_result["es_run_original"]
                result["es_mutation_score_original"] = evo_result["es_mutation_score_original"]
                result["es_test_path_original"] = evo_result["es_test_path_original"]

                # Buggy
                result["eo_compiled_buggy"] = evo_result["eo_compiled_buggy"]
                result["eo_run_buggy"] = evo_result["eo_run_buggy"]
                result["eo_mutation_score_buggy"] = evo_result["eo_mutation_score_buggy"]
                result["eo_test_path_buggy"] = evo_result["eo_test_path_buggy"]
                
                result["es_compiled_buggy"] = evo_result["es_compiled_buggy"]
                result["es_run_buggy"] = evo_result["es_run_buggy"]
                result["es_mutation_score_buggy"] = evo_result["es_mutation_score_buggy"]
                result["es_test_path_buggy"] = evo_result["es_test_path_buggy"]
                
                show_status = True

                if show_status:
                    print(Fore.GREEN + "############################# STATUS #############################", Style.RESET_ALL)
                    print_status(evo_result["eo_compiled_original"], "O_EvoOracle_COMPILE")
                    print_status(evo_result["eo_run_original"], "O_EvoOracle_RUN")

                    # print_status(evo_result["es_compiled_original"], "ES_ORG_COMPILE")
                    # print_status(evo_result["es_run_original"], "ES_ORG_RUN")
                    
                    print_status(evo_result["eo_compiled_buggy"], "B_EvoOracle_COMPILE")
                    print_status(evo_result["eo_run_buggy"], "B_EvoOracle_RUN")
                    
                    # print_status(evo_result["es_compiled_buggy"], "ES_BUG_COMPILE")
                    # print_status(evo_result["es_run_buggy"], "ES_BUG_RUN")

                if evo_result["eo_compiled_original"]:
                    break
                else:
                    print("Assertion compilation: " + Fore.CYAN + "FAILED", Style.RESET_ALL)
                    end_time = time.perf_counter()
            else:
                print("Assertion generation: " + Fore.RED + "FAILED", Style.RESET_ALL)
                end_time = time.perf_counter()
        
        result["attempts"] = rounds

    except Exception as e:
        print(Fore.RED + str(e), Style.RESET_ALL)
        end_time = time.perf_counter()
    
    # end_time = time.perf_counter()

    assertion_generation_time = (end_time - start_time) * 1000

    result["assertion_generation_time"] = assertion_generation_time
    result["prompts_and_responses"] = prompts_and_responses
    result["variant"] = variant.name
    
    return result

def print_status(status, message):
    if status:
        print(message + ": " + Fore.GREEN + "SUCCESS" + Style.RESET_ALL)
    else:
        print(message + ": " + Fore.RED + "FAIL" + Style.RESET_ALL)

def trim_string_to_substring(original_string, substring):
    # Find the index of the substring
    substring_index = original_string.find(substring)

    if substring_index != -1:
        # Trim the string to keep everything before and including the substring
        trimmed_string = original_string[:substring_index + len(substring)]
    else:
        # Substring not found, keep the original string as is
        trimmed_string = original_string

    return trimmed_string

def trim_string_to_desired_length(original_string, cutoff_length):
    # Trim the string
    trimmed_string = original_string[:cutoff_length]

    # Print the trimmed string
    print(trimmed_string)

    return trimmed_string

def trim_list_to_desired_size(original_list, cutoff_length):
    try:
        if not isinstance(original_list, list):
            original_list = json.loads(original_list)
        
        while len(original_list) > cutoff_length:
            original_list.pop()  
        return original_list
    except json.JSONDecodeError:
        return original_list

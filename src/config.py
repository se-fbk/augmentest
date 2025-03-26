import configparser
import os

config = configparser.ConfigParser()
config.read("../config/config.ini")

max_attempts = eval(config.get("DEFAULT", "max_attempts"))
MAX_PROMPT_TOKENS = eval(config.get("DEFAULT", "MAX_PROMPT_TOKENS"))

SP_TEMPLATE = config.get("DEFAULT", "SP_TEMPLATE")
EP_TEMPLATE = config.get("DEFAULT", "EP_TEMPLATE")
RAG_GEN_TEMPLATE = config.get("DEFAULT", "RAG_GEN_TEMPLATE")
RAG_SP_TEMPLATE = config.get("DEFAULT", "RAG_SP_TEMPLATE")

# LANGUAGE = config.get("DEFAULT", "LANGUAGE")
# GRAMMAR_FILE = config.get("DEFAULT", "GRAMMAR_FILE")
# PROGRAMMING_EXTENSION = config.get("DEFAULT", "GRAMMAR_FILE")

output_dir = config.get("DEFAULT", "output_dir")
db_json_file = config.get("DEFAULT", "db_json_file")
db_csv_file = config.get("DEFAULT", "db_csv_file")

DEFAULT_MODEL = config.get("DEFAULT", "DEFAULT_MODEL")
DEFAULT_VARIANT = config.get("DEFAULT", "DEFAULT_VARIANT")
DEFAULT_USE_COMMENTS = config.get("DEFAULT", "DEFAULT_USE_COMMENTS")

augmentest_csv_input = os.path.normpath(os.path.join(os.path.dirname(os.getcwd()), config.get("DEFAULT", "augmentest_csv_input").lstrip('/\\')))

final_result_file = os.path.normpath(os.path.join(os.path.dirname(os.getcwd()), config.get("DEFAULT", "final_result_file").lstrip('/\\')))

vector_store_json = os.path.normpath(os.path.join(os.path.dirname(os.getcwd()), config.get("DEFAULT", "vector_store_json").lstrip('/\\')))

class_info_output = config.get("DEFAULT", "class_info_output")

openai_api_key = eval(config.get("openai", "api_key"))
openai_model = config.get("openai", "model")

LLM_BASE_PATH = config.get("DEFAULT", "llm_base_path")

model = config.get("llm", "model")

def get_language(lang):
    return config.get(lang.upper(), "LANGUAGE")

def get_grammar(lang):
    return config.get(lang.upper(), "GRAMMAR_FILE")

def get_extension(lang):
    return config.get(lang.upper(), "EXTENSION")
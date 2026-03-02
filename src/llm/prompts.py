import jinja2
import os.path

from typing import Optional, Literal

try:
    # Create a jinja2 environment
    # Get the directory where THIS script is located (e.g., /app/src/llm)
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the 'prompt' folder relative to this script
    # Adjust the '..' levels based on your actual folder structure.
    # Example: If script is in /app/src/llm and prompts are in /app/src/prompts
    template_path = os.path.join(current_dir, "../../prompt")

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    print("LLM Prompt Templates loaded.")

except Exception as e:
    print("LLM Prompt Templates loading failed, exiting...", e)
    # TODO: Decide whether to exit the program or raise a proper initialization error.
    # Option A: hard exit
    # sys.exit(1)

    # Option B: raise to caller for agentic error propagation
    raise RuntimeError("Failed to load LLM prompt templates") from e

# Enumerate the "roles" / use cases if you want type safety
SystemPromptKey = Literal["assertion_default", "critic", "refiner"]


SYSTEM_MESSAGES = {
    "assertion_default": (
        "You are an AI assistant that generates and refines JUnit assertions "
        "for Java test methods. Output ONLY Java assertion code, no explanations."
    ),
    "critic": (
        "You are a strict code reviewer for JUnit tests. "
        "Given assertions and informal requirements, decide if the assertions "
        "match the requirements. Reply with either APPROVE or REJECT and a "
        "very short justification."
    ),
    "refiner": (
        "You improve existing JUnit assertions so that they better match the "
        "informal requirements and typical Java testing practices. "
        "REPLACE the assertion in the test case with the corrected version you proposed."
        "Return the corrected test case only. NO explanations."
    ),
    "compilation_fixer" : (
        "You are fixing compilation problems in JUnit test case. "
        "Fix the compilation problems based on the provided feedback. "
        "Return the corrected test case only. NO explanations."
    ),
    "formatter": (
        "As a strict JUnit test code readability expert, detect and fix any test smells in the "
        "given JUnit test code. Return ONLY the updated JUnit test code as PLAIN TEXT. "
        "NO explanations. NO markdown or other formatting characters should be returned."
    ),
}


def get_system_message(key: SystemPromptKey = "assertion_default") -> str:
    """
    Returns a system message for the given role/key.
    Falls back to the default assertion message if the key is unknown.
    """
    return SYSTEM_MESSAGES.get(key, SYSTEM_MESSAGES["assertion_default"])


def build_user_message(instruction: str, context: Optional[str] = None) -> str:
    """
    Builds a consistent user message.

    - If context is provided and non-empty:
        "### Context:\\n{context}\\n\\n### Instruction:\\n{instruction}"
    - If context is empty/None:
        "### Instruction:\\n{instruction}"
    """
    instruction = instruction.strip()

    if context is not None:
        context = context.strip()

    if context:
        return f"### Context:\n{context}\n\n### Instruction:\n{instruction}"

    return f"### Instruction:\n{instruction}"


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


def generate_messages(template_name, context):
    """
    This function generates messages before asking LLM, using templates.
    :param template_name: The template name of the user template.
    :param context: The context JSON file or dict to render the template.
    :return: A list of generated messages.
    """
    message = generate_prompt(template_name, context)

    return message
from gpt4all import GPT4All
from colorama import Fore, Style

from .base import LLMClient
from .prompts import (
    get_system_message,
    build_user_message,
    SystemPromptKey,
)
from src.config.config import DEFAULT_MODEL, LLM_BASE_PATH  # keep as-is


class GPT4AllModelClient(LLMClient):
    """
    GPT4All-based local LLM client.

    Uses the shared system prompts and user-message builder so that
    prompts are consistent with other backends (Llama.cpp, Gemini, etc.).
    """

    def __init__(self, system_prompt_key: SystemPromptKey = "assertion_default"):
        self.system_prompt_key = system_prompt_key

    def query(self, prompt: str, context_str: str = "") -> str:
        """
        - prompt: logical instruction (e.g. "Generate assertions for this test")
        - context_str: optional context (code, requirements, method name, etc.)
                       If empty, context is omitted from the message.
        """

        # Shared system message (not explicitly used by GPT4All API,
        # so we prepend it manually to the final text)
        system_message = get_system_message(self.system_prompt_key)

        # Shared user message builder (handles empty context)
        user_message = build_user_message(
            instruction=prompt,
            context=context_str or None,
        )

        # Final message sent to the model
        message = f"{system_message}\n\n{user_message}"

        try:
            model = GPT4All(DEFAULT_MODEL, model_path=LLM_BASE_PATH)

            print("Prompt: " + Fore.GREEN + message + Style.RESET_ALL)
            with model.chat_session():
                response = model.generate(message)
            print("Response: " + Fore.BLUE + response + Style.RESET_ALL)

            return response

        except Exception as e:
            print(Fore.RED + str(e) + Style.RESET_ALL)
            return ""

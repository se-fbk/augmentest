import os
import time
import logging
from openai import OpenAI
from colorama import Fore, Style

from .base import LLMClient
from .prompts import (
    get_system_message,
    build_user_message,
    SystemPromptKey
)


class OpenAIRagModelClient(LLMClient):
    """
    OpenAI RAG-enabled client.

    This implementation handles RAG-specific logic (like project_id)
    while adhering to the standard LLMClient query interface.
    """

    def __init__(
            self,
            project_id: str,
            model: str = "gpt-4o",
            max_retries: int = 7,  # Higher retry count as per your original RAG function
            initial_delay: float = 1.0,
            system_prompt_key: SystemPromptKey = "assertion_default",
    ):
        self.project_id = project_id
        self.model = model
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.system_prompt_key = system_prompt_key

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set for RAG client.")

        self.client = OpenAI(api_key=api_key)

    def query(self, prompt: str, context_str: str = "") -> str:
        """
        Executes a RAG-based query.
        Note: The 'context_str' here can be additional context,
        while the 'project_id' handles the retrieval-augmented portion.
        """
        system_content = get_system_message(self.system_prompt_key)

        # Combine instructions with provided context
        user_content = build_user_message(
            instruction=prompt,
            context=context_str or None
        )

        retries = 0
        delay = self.initial_delay

        while retries < self.max_retries:
            try:
                print(
                    Fore.CYAN + f"\n📡 Sending OpenAI RAG request (Project: {self.project_id}) (attempt {retries + 1})..." + Style.RESET_ALL)

                # Assuming your RAG implementation uses specific headers or
                # assistant tools. Here we apply the logic from your prompter:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": f"Project Context ID: {self.project_id}\n\n{user_content}"}
                    ],
                    temperature=0.7
                )

                cleaned = response.choices[0].message.content.strip()

                if cleaned:
                    print(Fore.GREEN + "✅ RAG response received" + Style.RESET_ALL)
                    return cleaned
                else:
                    print(Fore.RED + "⚠️ Empty RAG response. Retrying..." + Style.RESET_ALL)

            except Exception as e:
                print(Fore.RED + f"❌ RAG Exception: {str(e)}" + Style.RESET_ALL)
                logging.error(f"RAG exception for project {self.project_id}: {str(e)}")

            retries += 1
            if retries < self.max_retries:
                time.sleep(delay)
                delay *= 2

        return ""
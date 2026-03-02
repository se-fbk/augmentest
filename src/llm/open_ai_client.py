import os
import time
import logging
from typing import List, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from colorama import Fore, Style

from .base import LLMClient
from .prompts import (
    get_system_message,
    build_user_message,
    SystemPromptKey
)


class OpenAIModelClient(LLMClient):
    """
    OpenAI API client with:
      - shared system prompts
      - consistent user-message construction
      - exponential backoff retry
      - strict type-hinting for OpenAI message parameters
    """

    def __init__(
            self,
            model: str = "gpt-4o",
            max_retries: int = 3,
            initial_delay: float = 1.0,
            system_prompt_key: SystemPromptKey = "assertion_default",
    ):
        self.model = model
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.system_prompt_key = system_prompt_key

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment variables.")

        self.client = OpenAI(api_key=api_key)

    # ---------------------------------------------------------
    # PUBLIC API (consistent with all other LLM clients)
    # ---------------------------------------------------------
    def query(self, prompt: str, context_str: str = "") -> str:
        """
        Sends a prompt to OpenAI using:
          - standardized system prompt
          - standardized user message
          - built-in retry logic with exponential backoff
        """

        # 1. Build message content strings
        system_content = get_system_message(self.system_prompt_key)
        user_content = build_user_message(
            instruction=prompt,
            context=context_str or None,
        )

        # 2. Construct messages list using proper OpenAI types to avoid linter warnings
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

        retries = 0
        delay = self.initial_delay

        # -----------------------------------------------------
        #  RETRY LOOP
        # -----------------------------------------------------
        while retries < self.max_retries:
            try:
                print(
                    Fore.CYAN + f"\n📡 Sending OpenAI request ({self.model}) (attempt {retries + 1})..." + Style.RESET_ALL)

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=256,
                    top_p=1
                )

                cleaned = response.choices[0].message.content.strip()

                # Remove potential markdown formatting if model ignores system instructions
                if cleaned.startswith("```"):
                    # Basic cleanup for code blocks
                    lines = cleaned.splitlines()
                    if len(lines) > 2:
                        cleaned = "\n".join(lines[1:-1]).strip()

                print(Fore.GREEN + "✅ OpenAI response received" + Style.RESET_ALL)
                print("Prompt:", Fore.GREEN + user_content[:150] + "..." + Style.RESET_ALL)
                print("Response:", Fore.BLUE + cleaned + Style.RESET_ALL)

                return cleaned

            except Exception as e:
                print(Fore.RED + f"❌ OpenAI Exception: {str(e)}" + Style.RESET_ALL)
                logging.error(f"OpenAI exception: {str(e)}")

            # Exponential Backoff Logic
            retries += 1
            if retries < self.max_retries:
                print(
                    Fore.YELLOW
                    + f"⏳ Retrying in {delay} seconds (attempt {retries + 1}/{self.max_retries})..."
                    + Style.RESET_ALL
                )
                time.sleep(delay)
                delay *= 2

        print(Fore.RED + "❌ Max retries reached. OpenAI API failed." + Style.RESET_ALL)
        return ""
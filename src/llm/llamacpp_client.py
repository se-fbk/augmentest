# augmentest/llm/llamacpp_client.py

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from colorama import Fore, Style

from .base import LLMClient
from .prompts import get_system_message, build_user_message, SystemPromptKey


class LLamaCPPModelClient(LLMClient):
    """
    LLM client for a local Llama.cpp-compatible server, exposed via
    an OpenAI-compatible Chat API (langchain_openai.ChatOpenAI).

    Uses shared system prompts and a consistent user-message format.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str = "nachiave",
        system_prompt_key: SystemPromptKey = "assertion_default",
    ):
        self.llm = ChatOpenAI(
            base_url="http://localhost:8000",
            api_key="nachiave",
        )
        self.system_prompt_key = system_prompt_key

    def query(self, prompt: str, context_str: str = "") -> str:
        """
        - `prompt`: logical instruction (e.g., "Generate assertions for this test")
        - `context_str`: optional context (method name, code, requirements, etc.)
          If empty, it is NOT included in the final message.
        """

        system_msg = SystemMessage(
            content=get_system_message(self.system_prompt_key)
        )

        user_content = build_user_message(
            instruction=prompt,
            context=context_str or None,
        )
        user_msg = HumanMessage(content=user_content)

        try:
            response = self.llm.invoke([system_msg, user_msg])
            text = response.content

            print("Prompt:", Fore.GREEN + user_msg.content + Style.RESET_ALL)
            print("Response:", Fore.BLUE + text + Style.RESET_ALL)

            return text

        except Exception as e:
            print(Fore.RED + f"[LLM ERROR] {e}" + Style.RESET_ALL)
            return ""

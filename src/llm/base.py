from typing import Protocol

class LLMClient(Protocol):
    """
    Minimal interface for all LLM backends used by AugmenTest.
    """
    def query(self, prompt: str, context_str: str = "") -> str:
        ...

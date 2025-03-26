from enum import Enum

class Variants(Enum):
    SIMPLE_PROMPT = 1
    EXTENDED_PROMPT = 2
    RAG = 3
    SIMPLE_PROMPT_WITH_RAG = 4
    TOGA_DEFAULT = 5
    TOGA_UNFILTERED = 6
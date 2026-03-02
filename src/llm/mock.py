from src.llm.base import LLMClient

class MockModelWrapper(LLMClient):
    """
    Deterministic mock LLM used for testing the agentic workflow.
    It simulates:
      - Oracle generation
      - Critic behavior
      - Refinement cycles

    This allows full agent testing without calling any real LLM.
    """

    def __init__(self):
        # You can store internal counters if needed
        self.call_count = 0

    def query(self, prompt: str, context_str: str = "") -> str:
        """
        Respond based on the role implied in the prompt.
        The rules here mirror typical LLM interactions:
          - If prompt contains "[ACT AS CRITIC]": return APPROVE/REJECT
          - Otherwise: simulate assertion generation or refinement

        Args:
            prompt: The instruction/prompt text
            context_str: Context such as method name or attempt count

        Returns:
            A deterministic mock assertion or critic decision.
        """
        self.call_count += 1

        # ----------------------------------------------------------
        # 1. CRITIC BEHAVIOR
        # ----------------------------------------------------------
        if "[ACT AS CRITIC]" in prompt:
            # Reject assertions containing obvious mistakes
            if "Buggy" in prompt or "0, result" in prompt:
                return "REJECT: Assertions do not match requirements."
            return "APPROVE"

        # ----------------------------------------------------------
        # 2. GENERATOR + REFINER BEHAVIOR
        # ----------------------------------------------------------
        # Simulate test-specific behaviors
        method = context_str.lower()

        # Fake scenario for testSum
        if "testsum" in method:
            if "attempt 1" in method:
                # Simulate a bad first attempt
                return "assertEquals(0, result); // Buggy"
            # Second and later attempts produce correct answer
            return "assertEquals(15, result); // Correct (5+10)"

        # Fake scenario for testDivide
        if "testdivide" in method:
            return "assertEquals(5, result); // Correct (10/2)"

        # Default fallback assertion
        return "assertNotNull(result);"

import os, re, json, time, logging, requests
from colorama import Fore, Style

from .base import LLMClient
from .prompts import (
    get_system_message,
    build_user_message,
    SystemPromptKey
)


class GeminiModelClient(LLMClient):
    """
    Google Gemini API client with:
      - shared system prompts
      - consistent user-message construction
      - automatic removal of empty context sections
      - exponential backoff retry
    """

    def __init__(
        self,
        model: str = "gemini-3-flash-preview",
        max_retries: int = 3,
        initial_delay: float = 1.0,
        system_prompt_key: SystemPromptKey = "assertion_default",
    ):
        self.model = model
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.system_prompt_key = system_prompt_key

        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set in environment variables.")

        self.url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )

    # ---------------------------------------------------------
    # INTERNAL HELPERS
    # ---------------------------------------------------------
    def _extract_text(self, candidate_obj):
        try:
            text = candidate_obj["content"]["parts"][0]["text"]
        except Exception:
            return ""

        # TODO why did Shaker remove the *??
        cleaned = text #re.sub(r'\*\*|\*|`|<.*?>', '', text).strip()

        # Handle cases where Gemini prepends "json"
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

        return cleaned

    # ---------------------------------------------------------
    # PUBLIC API (consistent with all other LLM clients)
    # ---------------------------------------------------------
    def query(self, prompt: str, context_str: str = "") -> str:
        """
        Sends a prompt to the Gemini API using:
          - standardized system prompt
          - standardized user message
          - optional context handling
        """

        # Build SYSTEM message (same as other clients)
        system_message = get_system_message(self.system_prompt_key)

        # Build USER message using shared helper
        user_message_text = build_user_message(
            instruction=prompt,
            context=context_str or None,   # omit when empty
        )

        # Gemini does not use system/user roles explicitly like OpenAI,
        # so we inject system prompt ourselves:
        full_prompt = f"{system_message}\n\n{user_message_text}"

        payload = {
            "contents": [
                {"parts": [{"text": full_prompt}]}
            ]
        }

        retries = 0
        delay = self.initial_delay

        # -----------------------------------------------------
        #  RETRY LOOP
        # -----------------------------------------------------
        while retries < self.max_retries:
            try:
                print(Fore.CYAN + f"\n📡 Sending Gemini request (attempt {retries+1})..." + Style.RESET_ALL)

                response = requests.post(
                    self.url,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(payload),
                )

                if response.status_code == 200:
                    print(Fore.GREEN + "✅ Gemini response received" + Style.RESET_ALL)
                    result = response.json()

                    candidate = result["candidates"][0]
                    cleaned = self._extract_text(candidate)

                    print("Prompt:", Fore.GREEN + full_prompt + Style.RESET_ALL)
                    print("Response:", Fore.BLUE + cleaned + Style.RESET_ALL)

                    return cleaned

                # Non-200 → retry
                print(Fore.RED + f"❌ Gemini returned {response.status_code}" + Style.RESET_ALL)
                logging.error(f"Gemini error {response.status_code}: {response.text}")

            except Exception as e:
                print(Fore.RED + f"❌ Exception: {str(e)}" + Style.RESET_ALL)
                logging.error(f"Gemini exception: {str(e)}")

            # Retry logic
            retries += 1
            if retries < self.max_retries:
                print(
                    Fore.YELLOW
                    + f"⏳ Retrying in {delay} seconds (attempt {retries+1}/{self.max_retries})..."
                    + Style.RESET_ALL
                )
                time.sleep(delay)
                delay *= 2  # exponential backoff

        print(Fore.RED + "❌ Max retries reached. Gemini API failed." + Style.RESET_ALL)
        return ""

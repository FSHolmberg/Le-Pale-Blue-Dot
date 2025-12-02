import re
from src.agents.llm_client import LLMClient


class Bart:
    """Bart: the bartender. Probes for clarity, suggests antifragile paths."""

    def __init__(self, prompt: str | None = None) -> None:
        self.prompt = prompt or "You are Bart, the bartender."
        self.llm = LLMClient()

    def respond(self, text: str) -> str:
        if not text or not text.strip():
            return "Say something."

        try:
            response = self.llm.call(
                system_prompt=self.prompt,
                user_text=text,
                max_tokens=150,
            )
            # Strip stage directions
            response = re.sub(r'\*[^*]*\*', '', response).strip()
            return response
        except Exception as e:
            return "Bart: Something's off. Try again in a moment."
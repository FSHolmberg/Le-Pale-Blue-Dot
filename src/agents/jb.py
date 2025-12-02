import re
from src.agents.llm_client import LLMClient


class JB:
    """JB: Linguistic critic. Triggers on language quality issues."""

    def __init__(self, prompt: str | None = None) -> None:
        self.prompt = prompt or "You are JB, a language critic."
        self.llm = LLMClient()

    def respond(self, text: str) -> str:
        """
        Critique user's language using Claude API.
        
        Args:
            text: User message (or "jb" trigger)
            
        Returns:
            JB's critique
        """
        if not text or not text.strip():
            return "Speak clearly."

        # If just "jb" trigger, acknowledge
        if text.strip().lower() == "jb":
            return "JB: I'm listening."

        try:
            response = self.llm.call(
                system_prompt=self.prompt,
                user_text=text,
                max_tokens=200,
            )
            # Remove asterisks around single words (emphasis), remove entire multi-word phrases (stage directions)
            response = re.sub(r'\*(\w+)\*', r'\1', response)  # *word* -> word
            response = re.sub(r'\*[^*]*\s+[^*]+\*', '', response)  # Remove multi-word stage directions
            response = response.strip()
            return response.strip()
        
        except Exception as e:
            return f"JB error: {str(e)}"
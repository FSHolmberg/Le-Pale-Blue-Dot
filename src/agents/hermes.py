import re
from src.agents.llm_client import LLMClient


class Hermes:
    """Hermes: Ethical oversight through Camusian philosophy."""

    def __init__(self, prompt: str | None = None) -> None:
        self.prompt = prompt or "You are Hermes, an ethical guide."
        self.llm = LLMClient()

    def respond(self, text: str) -> str:
        """
        Provide ethical perspective or crisis intervention.
        
        Args:
            text: User message (or "hermes" trigger)
            
        Returns:
            Hermes's response
        """
        if not text or not text.strip():
            return "I'm listening."

        # If just "hermes" trigger, acknowledge
        if text.strip().lower() == "hermes":
            return "Hermes: What's on your mind?"

        try:
            response = self.llm.call(
                system_prompt=self.prompt,
                user_text=text,
                max_tokens=300,
            )
            # Remove asterisks around single words (emphasis), remove entire multi-word phrases (stage directions)
            response = re.sub(r'\*(\w+)\*', r'\1', response)  # *word* -> word
            response = re.sub(r'\*[^*]*\s+[^*]+\*', '', response)  # Remove multi-word stage directions
            response = response.strip()
            return response
        
        except Exception as e:
            return f"Hermes error: {str(e)}"

import re
from src.agents.llm_client import LLMClient


class Bernie:
    """Bernie"""

    def __init__(self, prompt: str | None = None) -> None:
        self.prompt = prompt or "You are Bernie, the friendly regular."
        self.llm = LLMClient()

    def respond(self, text: str) -> str:
        """
        Respond to user input using Claude API.
        
        Args:
            text: User message
            
        Returns:
            Bernie's response
        """
        if not text or not text.strip():
            return "Should I read you a story?"

        try:
            response = self.llm.call(
                system_prompt=self.prompt,
                user_text=text,
                max_tokens=200,
            )
            # Strip stage directions
            response = re.sub(r'\*[^*]*\*', '', response).strip()
            return response
        except Exception as e:
            # Show actual error for debugging
            return f"Bernie error: {str(e)}"
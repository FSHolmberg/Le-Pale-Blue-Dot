
"""
Blanca: The Moderator

Inspired by José Raúl Capablanca - tactical, impartial chess referee.
Manages conversation flow, notices patterns, suggests moves without ego.
"""

from src.agents.llm_client import LLMClient


class Blanca:
    """Moderator agent - notices stuck conversations, suggests topic changes."""
    
    def __init__(self, prompt: str):
        """
        Args:
            prompt: System prompt defining Blanca's personality and role
        """
        self.llm = LLMClient()
        self.system_prompt = prompt
    
    def respond(self, user_text: str) -> str:
        """
        Generate Blanca's response to user input.
        
        Args:
            user_text: The user's message (with "blanca:" prefix removed)
            
        Returns:
            Blanca's tactical observation or suggestion
        """
        messages = [
            {"role": "user", "content": user_text}
        ]
        
        return self.llm.call(
            system_prompt=self.system_prompt,
            user_text=user_text,
            max_tokens=50  # Blanca is tactical - brief observations only
        )
    
    def scan_for_violations(self, user_text: str) -> tuple[bool, str]:
        """
        Check if user message violates conversation rules (CAPS, abuse, etc.).
        
        Args:
            user_text: Raw user input to scan
            
        Returns:
            (has_violation, warning_message) - If no violation, warning is empty
        """
        # Check for excessive CAPS (>70% of message)
        if len(user_text) > 10:  # Only check messages with substance
            caps_count = sum(1 for c in user_text if c.isupper())
            total_letters = sum(1 for c in user_text if c.isalpha())
            if total_letters > 0 and (caps_count / total_letters) > 0.7:
                return (True, "Lower your voice. This is a bar, not a stadium.")
        
        # Check for empty/whitespace-only messages
        if not user_text.strip():
            return (True, "Speak or pass. Don't waste the table's time.")
        
        # No violation detected
        return (False, "")
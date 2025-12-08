
import os
import anthropic


class LLMClient:
    """Wrapper for Claude API calls. Used by all agents."""

    def __init__(self, model: str = "claude-sonnet-4-5-20250929") -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set in this process")
        
        self.client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
        self.model = model

    def call(self, system_prompt: str, user_text: str, max_tokens: int = 150, use_cache: bool = True) -> str:
        """
        Call Claude with system prompt + user text.
        Returns response text or raises exception on failure.
        
        Args:
            system_prompt: System instruction for Claude
            user_text: User message
            max_tokens: Max tokens in response
            use_cache: If True, mark system prompt for caching (5min TTL)
            
        Returns:
            Claude's response as string
            
        Raises:
            RuntimeError: If API call fails
        """
        try:
            # Build system parameter with optional caching
            if use_cache:
                system = [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
            else:
                system = system_prompt
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[
                    {"role": "user", "content": user_text}
                ],
            )
            
            # Log cache performance
            usage = message.usage
            if usage.cache_read_input_tokens > 0:
                print(f"Cache hit: {usage.cache_read_input_tokens} tokens read from cache")
            
            return message.content[0].text
        except anthropic.APIError as e:
            raise RuntimeError(f"Claude API error: {e}")

    def call_safe(self, system_prompt: str, user_text: str, fallback: str = "") -> str:
            """
            Call Claude, return fallback if it fails.
            Use this for non-critical calls where silence is acceptable.
            
            Args:
                system_prompt: System instruction for Claude
                user_text: User message
                fallback: Text to return if call fails
                
            Returns:
                Claude's response or fallback string
            """
            try:
                return self.call(system_prompt, user_text)
            except Exception as e:
                print(f"LLM call failed: {e}")
                return fallback
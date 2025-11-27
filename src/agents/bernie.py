

class Bernie:
    def __init__(self, prompt: str | None = None) -> None:
        self.prompt = prompt
        
    def respond(self, text: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            return "Bernie: you'll have to say something before we can unpack it."
        return f"Bernie: let's sit with that for a moment - {cleaned!r}"
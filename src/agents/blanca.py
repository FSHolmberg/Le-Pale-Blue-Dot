

class Blanca:
    def __init__(self, prompt: str | None = None) -> None:
        self.prompt = prompt
        
    def respond(self, text: str) -> str:
        return "Blanca is watching."

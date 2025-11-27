


class Bart:
    def __init__(self, prompt: str | None = None) -> None:
        self.prompt = prompt

    def respond(self, text: str) -> str:
        cleaned = text.strip()

        if not cleaned:
            return "Say something."

        if "?" in cleaned:
            return f"You ask a lot of questions. This one was: {cleaned!r}"

        if len(cleaned) < 10:
            return f"That's not much to work with: {cleaned!r}."

        return f"Alright. I heard: {cleaned!r}"

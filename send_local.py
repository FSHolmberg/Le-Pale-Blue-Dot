

from time import time

from src.router import Router
from src.schemas.message import Message

def main() -> None:
    router = Router()

    while True:
        user_text = input("You: ").strip()
        if user_text.lower() in {"quit", "exit"}:
            break

        msg = Message(user_id="cli", text=user_text, timestamp=time())
        agent, reply = router.handle(msg)
        print(f"{agent}> {reply}")

if __name__ == "__main__":
    main()

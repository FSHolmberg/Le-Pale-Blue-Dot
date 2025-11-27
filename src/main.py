from fastapi import FastAPI
from src.router import Router
from src.schemas.message import Message
from src.history import MessageHistory
from src.config.loader import Config

app = FastAPI()
history = MessageHistory()
config = Config()
router = Router(history=history, config=config)

@app.post("/chat")
def chat(msg: Message):
    agent_name, reply = router.handle(msg)
    return {"agent": agent_name, "reply": reply}

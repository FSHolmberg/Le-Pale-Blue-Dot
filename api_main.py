

from fastapi import FastAPI

from src.router import Router
from src.schemas.message import Message

app = FastAPI()
router = Router()  # Router sets up config, history, logging

@app.post("/chat")
def chat(msg: Message):
    agent_name, reply = router.handle(msg)
    return {"agent": agent_name, "reply": reply}

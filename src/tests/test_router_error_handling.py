

import pytest
from src.router import Router
from src.schemas.message import Message

def test_router_fallback_on_agent_exception(monkeypatch):
    router = Router()

    def boom(self, text):
        raise RuntimeError("boom")

    monkeypatch.setattr(router.bart, "respond", boom)

    msg = Message(user_id="x", text="hello", timestamp=0.0)
    agent, reply = router.handle(msg)

    assert agent == "blanca"
    assert "Cleaner needs the room" in reply

def test_router_fallback_on_empty_message():
    router = Router()

    msg = Message(user_id="x", text="   ", timestamp=0.0)
    agent, reply = router.handle(msg)

    assert agent == "blanca"
    assert "Cleaner needs the room" in reply

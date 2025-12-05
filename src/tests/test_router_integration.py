
import pytest
pytestmark = pytest.mark.slow 

from time import time
from src.router import Router
from src.schemas.message import Message

def test_router_blanca():
    r = Router()
    msg = Message(user_id="x", text="HELLO", timestamp=0.0)
    agent, reply = r.handle(msg)
    assert agent == "blanca"
    assert reply == "Lower your voice. This is a bar, not a stadium."

def test_router_bart():
    r = Router()
    msg = Message(user_id="x", text="hello", timestamp=0.0)
    agent, reply = r.handle(msg)
    assert agent == "bart"

def test_router_selects_bernie():
    router = Router()
    msg = Message(user_id="test", text="bernie: I'm tired.", timestamp=0.0)
    agent, reply = router.handle(msg)
    assert agent == "bernie"

def test_router_selects_bukowski():
    router = Router()
    msg = Message(user_id="test", text="bukowski: I'm tired.", timestamp=0.0)
    agent, reply = router.handle(msg)
    assert agent == "bukowski"
    assert reply.startswith("Unclear instruction.")

def test_router_selects_hermes():
    router = Router()
    msg = Message(user_id="test", text="hermes: I'm tired.", timestamp=0.0)
    agent, reply = router.handle(msg)
    assert agent == "hermes"


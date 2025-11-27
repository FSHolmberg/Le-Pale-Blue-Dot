from time import time

from src.router import Router
from src.schemas.message import Message


def test_router_selects_jb():
    router = Router()
    msg = Message(
        user_id="test",
        text="jb",
        timestamp=time(),
    )

    agent, reply = router.handle(msg)

    assert agent == "jb"
    assert "JB" in reply

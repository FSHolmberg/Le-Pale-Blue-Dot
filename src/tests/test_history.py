import pytest
pytestmark = pytest.mark.slow

from src.history import MessageHistory
from src.router import Router
from src.schemas.message import Message


def test_router_adds_turn_to_history():
    history = MessageHistory(max_turns_per_user=10)
    router = Router(history=history)

    msg = Message(user_id="u1", text="hello", timestamp=0.0)
    agent, reply = router.handle(msg)

    recent = history.get_recent("u1")
    assert len(recent) == 1

    turn = recent[0]
    assert turn.user_id == "u1"
    assert turn.agent == agent
    assert turn.user_text == "hello"
    assert turn.reply_text == reply

def test_history_prunes_old_turns():
    history = MessageHistory(max_turns_per_user=2)
    router = Router(history=history)

    router.handle(Message(user_id="u1", text="1", timestamp=0.0))
    router.handle(Message(user_id="u1", text="2", timestamp=0.1))
    router.handle(Message(user_id="u1", text="3", timestamp=0.2))

    recent = history.get_recent("u1")

    assert len(recent) == 2
    assert recent[0].user_text == "2"
    assert recent[1].user_text == "3"


def test_get_recent_with_limit():
    history = MessageHistory(max_turns_per_user=10)
    router = Router(history=history)

    router.handle(Message(user_id="u1", text="a", timestamp=0.0))
    router.handle(Message(user_id="u1", text="b", timestamp=0.1))
    router.handle(Message(user_id="u1", text="c", timestamp=0.2))

    recent = history.get_recent("u1", limit=2)

    assert len(recent) == 2
    assert recent[0].user_text == "b"
    assert recent[1].user_text == "c"

def test_history_stores_messages_in_chronological_order():
    history = MessageHistory(max_turns_per_user=10)

    history.add_turn(
        user_id="u1",
        agent="bart",
        user_text="first",
        reply_text="reply1",
        ts=1.0)
    history.add_turn(
        user_id="u1",
        agent="bart",
        user_text="second",
        reply_text="reply2",
        ts=2.0)

    turns = history.get_recent("u1", limit=10)
    user_texts = [t.user_text for t in turns]
    assert user_texts == ["first", "second"]
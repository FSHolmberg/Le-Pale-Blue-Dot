

import time

from src.agents import bukowski
from src.history import MessageHistory
from src.agents.bukowski_ledger import BukowskiLedger

def _make_history(user_id: str, texts: list[str]) -> MessageHistory:
    h = MessageHistory()
    ts = 1_000.0
    for t in texts:
        h.add_turn(
            user_id=user_id,
            agent="bart",
            user_text=t,
            reply_text="",
            ts=ts,
        )
        ts += 1.0
    return h

def test_bukowski_note_logs_entry():
    user_id = "u1"
    history = _make_history(user_id, ["First thing", "Second thing"])
    ledger = BukowskiLedger()
    now = 1234.5

    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: note",
        history=history,
        ledger=ledger,
        now=now)

    assert reply.startswith("Logged.")

    last_list = ledger.get_last(1)
    assert len(last_list) == 1
    last = last_list[0]
    assert "First thing" in last.text or "Second thing" in last.text



def test_bukowski_show_last_empty():
    user_id = "u1"
    history = MessageHistory()
    ledger = BukowskiLedger()

    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: show last",
        history=history,
        ledger=ledger,
        now=time.time())

    assert reply == "No entries. Ledger is clean."


def test_bukowski_delete_last():
    user_id = "u1"
    history = MessageHistory()
    ledger = BukowskiLedger()
    ledger.log("test entry")

    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: delete last",
        history=history,
        ledger=ledger,
        now=time.time())

    assert reply == "Last entry removed."
    assert ledger.get_last() == []


def test_bukowski_help():
    user_id = "u1"
    history = MessageHistory()
    ledger = BukowskiLedger()

    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: help",
        history=history,
        ledger=ledger,
        now=time.time(),
    )

    assert "bukowski: note" in reply
    assert "bukowski: show last" in reply

def test_bukowski_show_last_after_note():
    user_id = "u1"
    history = _make_history(user_id, ["Alpha", "Beta"])
    ledger = BukowskiLedger()

    bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: note",
        history=history,
        ledger=ledger,
        now=123.0)

    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: show last",
        history=history,
        ledger=ledger,
        now=124.0)

    assert reply.startswith("Last entry:")
    assert "Alpha" in reply or "Beta" in reply

def test_parse_bukowski_commands():
    assert bukowski.parse_bukowski_command("bukowski: note") == "note"
    assert bukowski.parse_bukowski_command("bukowski: show last") == "show_last"
    assert bukowski.parse_bukowski_command("bukowski: delete last") == "delete_last"
    assert bukowski.parse_bukowski_command("bukowski: help") == "help"

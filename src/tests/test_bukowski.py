import pytest
pytestmark = pytest.mark.slow

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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

def test_bukowski_command_variations():
    """Test all command aliases work."""
    user_id = "u1"
    history = _make_history(user_id, ["Test message"])
    ledger = BukowskiLedger()
    
    # "log" should work like "note"
    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: log",
        history=history,
        ledger=ledger,
        now=100.0
    )
    assert reply.startswith("Logged.")
    
    # "last" should work like "show last"
    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: last",
        history=history,
        ledger=ledger,
        now=101.0
    )
    assert "Last entry:" in reply
    
    # "remove last" should work like "delete last"
    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: remove last",
        history=history,
        ledger=ledger,
        now=102.0
    )
    assert reply == "Last entry removed."

def test_bukowski_case_insensitive():
    """Commands should work regardless of case."""
    user_id = "u1"
    history = _make_history(user_id, ["Test"])
    ledger = BukowskiLedger()
    
    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="BUKOWSKI: NOTE",
        history=history,
        ledger=ledger,
        now=100.0
    )
    assert reply.startswith("Logged.")
    
    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="BuKoWsKi: ShOw LaSt",
        history=history,
        ledger=ledger,
        now=101.0
    )
    assert "Last entry:" in reply

def test_bukowski_mechanical_tone():
    """Bukowski should have zero personality - just mechanical output."""
    user_id = "u1"
    history = _make_history(user_id, ["Emotional message"])
    ledger = BukowskiLedger()
    
    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: note",
        history=history,
        ledger=ledger,
        now=100.0
    )
    
    # Should not contain personality markers
    forbidden_words = [
        "nice", "great", "excellent", "good job", "well done",
        "sorry", "unfortunately", "glad", "happy", "pleased",
        "!", # No excitement
    ]
    
    reply_lower = reply.lower()
    for word in forbidden_words:
        assert word not in reply_lower, f"Bukowski showed personality: '{word}'"
    
    # Should be terse
    assert len(reply.split()) < 10, "Bukowski response too verbose"

def test_bukowski_truncates_long_messages():
    """Messages over 160 chars should be truncated."""
    user_id = "u1"
    
    # Create a very long message
    long_text = "A" * 200  # 200 characters
    history = _make_history(user_id, [long_text])
    ledger = BukowskiLedger()
    
    bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: note",
        history=history,
        ledger=ledger,
        now=100.0
    )
    
    last_entry = ledger.get_last(1)[0]
    
    # Check that the entry was truncated (has "...")
    assert "..." in last_entry.text, "Long message not truncated"
    
    # Check that no single line segment is over 160 chars
    segments = last_entry.text.split(" | ")
    for seg in segments:
        assert len(seg) <= 160, f"Segment too long: {len(seg)} chars"

def test_bukowski_multiple_sequential_notes():
    """Multiple notes should stack in ledger."""
    user_id = "u1"
    history1 = _make_history(user_id, ["First conversation"])
    history2 = _make_history(user_id, ["Second conversation"])
    ledger = BukowskiLedger()
    
    # Log first note
    bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: note",
        history=history1,
        ledger=ledger,
        now=100.0
    )
    
    # Log second note
    bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: note",
        history=history2,
        ledger=ledger,
        now=200.0
    )
    
    # Should have 2 entries
    all_entries = ledger.get_last(10)
    assert len(all_entries) == 2
    
    # Most recent should be second conversation
    last = all_entries[-1]
    assert "Second conversation" in last.text

def test_bukowski_empty_history_logs():
    """Logging with no conversation history should not crash."""
    user_id = "u1"
    history = MessageHistory()  # Empty
    ledger = BukowskiLedger()
    
    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: note",
        history=history,
        ledger=ledger,
        now=100.0
    )
    
    assert reply.startswith("Logged.")
    
    # Check what was logged
    last_entry = ledger.get_last(1)[0]
    assert "Empty state" in last_entry.text or "No recent conversation" in last_entry.text

def test_bukowski_unknown_command():
    """Unknown commands should show help."""
    user_id = "u1"
    history = MessageHistory()
    ledger = BukowskiLedger()
    
    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="bukowski: foobar",
        history=history,
        ledger=ledger,
        now=100.0
    )
    
    # Should explain available commands
    assert "bukowski: note" in reply
    assert "bukowski: show last" in reply
    assert "bukowski: delete last" in reply

def test_bukowski_no_prefix():
    """'bukowski:' prefix should be optional."""
    user_id = "u1"
    history = _make_history(user_id, ["Test"])
    ledger = BukowskiLedger()
    
    # Without prefix - command should still work
    # (Router adds "bukowski:" but testing parser flexibility)
    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="note",  # No "bukowski:" prefix
        history=history,
        ledger=ledger,
        now=100.0
    )
    
    assert reply.startswith("Logged.")

def test_bukowski_whitespace_handling():
    """Extra whitespace should not break commands."""
    user_id = "u1"
    history = _make_history(user_id, ["Test"])
    ledger = BukowskiLedger()
    
    reply = bukowski.handle_bukowski(
        user_id=user_id,
        raw_text="  bukowski:    note   ",
        history=history,
        ledger=ledger,
        now=100.0
    )
    
    assert reply.startswith("Logged.")
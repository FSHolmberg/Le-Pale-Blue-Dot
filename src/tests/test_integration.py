import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import time
from src.router import Router
from src.history import MessageHistory
from dataclasses import dataclass


@dataclass
class Message:
    """Simple message structure for testing."""
    user_id: str
    text: str
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


def test_basic_routing():
    """Test that messages route to correct agents."""
    router = Router()
    
    # Test Bart routing (default and explicit)
    msg = Message(user_id="u1", text="hello")
    agent, reply = router.handle(msg)
    assert agent == "bart", f"Default routing failed, got agent={agent}"
    
    msg = Message(user_id="u1", text="bart: help me think")
    agent, reply = router.handle(msg)
    assert agent == "bart"
    
    # Test Bernie routing
    msg = Message(user_id="u1", text="bernie: tell me something nice")
    agent, reply = router.handle(msg)
    assert agent == "bernie"
    
    # Test JB routing
    msg = Message(user_id="u1", text="jb: is this phrasing correct?")
    agent, reply = router.handle(msg)
    assert agent == "jb"
    
    # Test Blanca routing
    msg = Message(user_id="u1", text="blanca: I'm stuck")
    agent, reply = router.handle(msg)
    assert agent == "blanca"
    
    print("✓ Basic routing works")

def test_bukowski_commands():
    """Test Bukowski ledger commands."""
    router = Router()
    
    # Add some history first
    msg1 = Message(user_id="u1", text="First message")
    router.handle(msg1)
    
    msg2 = Message(user_id="u1", text="Second message")
    router.handle(msg2)
    
    # Test note command
    msg = Message(user_id="u1", text="bukowski: note")
    agent, reply = router.handle(msg)
    assert agent == "bukowski"
    assert reply.startswith("Logged"), f"Unexpected reply: {reply}"
    
    # Test show last command
    msg = Message(user_id="u1", text="bukowski: show last")
    agent, reply = router.handle(msg)
    assert agent == "bukowski"
    assert "Last entry:" in reply, f"Unexpected reply: {reply}"
    
    # Test delete last command
    msg = Message(user_id="u1", text="bukowski: delete last")
    agent, reply = router.handle(msg)
    assert agent == "bukowski"
    assert reply == "Last entry removed."
    
    print("✓ Bukowski commands work")

def test_blanca_pre_router_scan():
    """Test that Blanca intercepts violations before routing."""
    router = Router()
    
    # Test CAPS violation
    msg = Message(user_id="u1", text="WHY WON'T YOU HELP ME?!")
    agent, reply = router.handle(msg)
    assert agent == "blanca", f"CAPS not intercepted, got agent={agent}"
    assert "voice" in reply.lower() or "stadium" in reply.lower()
    
    # Test empty message
    msg = Message(user_id="u1", text="   ")
    agent, reply = router.handle(msg)
    assert agent == "blanca", f"Empty message not intercepted, got agent={agent}"
    
    # Test normal message passes through
    msg = Message(user_id="u1", text="Can you help me?")
    agent, reply = router.handle(msg)
    assert agent == "bart", f"Normal message was blocked, got agent={agent}"
    
    print("✓ Blanca pre-router scan works")

def test_crisis_detection():
    """Test that crisis language routes to Hermes."""
    router = Router()
    
    crisis_phrases = [
        "I want to kill myself",
        "I'm going to hurt myself",
        "I want to end it all",
        "I'm thinking about suicide"
    ]
    
    for phrase in crisis_phrases:
        msg = Message(user_id="u1", text=phrase)
        agent, reply = router.handle(msg)
        assert agent == "hermes", f"Crisis phrase not detected: '{phrase}', got agent={agent}"
    
    # Test non-crisis message doesn't trigger Hermes
    msg = Message(user_id="u1", text="I'm sad today")
    agent, reply = router.handle(msg)
    assert agent != "hermes", "Non-crisis message triggered Hermes"
    
    print("✓ Crisis detection works")

def test_mute_unmute():
    """Test agent muting and unmuting."""
    router = Router()
    
    # Mute Bart
    msg = Message(user_id="u1", text="mute bart")
    agent, reply = router.handle(msg)
    assert agent == "system"
    assert "muted" in reply.lower()
    assert "bart" in router.muted_agents
    
    # Unmute Bart
    msg = Message(user_id="u1", text="unmute bart")
    agent, reply = router.handle(msg)
    assert agent == "system"
    assert "unmuted" in reply.lower()
    assert "bart" not in router.muted_agents
    
    # Test invalid agent name
    msg = Message(user_id="u1", text="mute invalid_agent")
    agent, reply = router.handle(msg)
    assert "unknown" in reply.lower() or "invalid" in reply.lower()
    
    print("✓ Mute/unmute works")

def test_conversation_history():
    """Test that conversation history persists across messages."""
    history = MessageHistory()
    router = Router(history=history)
    
    # Send multiple messages
    msg1 = Message(user_id="u1", text="First message")
    router.handle(msg1)
    
    msg2 = Message(user_id="u1", text="Second message")
    router.handle(msg2)
    
    msg3 = Message(user_id="u1", text="Third message")
    router.handle(msg3)
    
    # Check history has all messages
    all_turns = history.get_recent(user_id="u1", limit=10)
    assert len(all_turns) >= 3, f"History not tracking, only {len(all_turns)} turns"
    
    print("✓ Conversation history persists")

def test_multi_agent_conversation():
    """Test switching between agents in conversation."""
    router = Router()
    
    # Talk to Bart
    msg = Message(user_id="u1", text="bart: help me decide something")
    agent1, reply1 = router.handle(msg)
    assert agent1 == "bart"
    
    # Switch to Bernie
    msg = Message(user_id="u1", text="bernie: tell me something positive")
    agent2, reply2 = router.handle(msg)
    assert agent2 == "bernie"
    
    # Switch to JB
    msg = Message(user_id="u1", text="jb: how's my grammar?")
    agent3, reply3 = router.handle(msg)
    assert agent3 == "jb"
    
    # Back to Bart
    msg = Message(user_id="u1", text="bart: what do you think?")
    agent4, reply4 = router.handle(msg)
    assert agent4 == "bart"
    
    print("✓ Multi-agent conversation works")

def test_case_insensitive_routing():
    """Test that agent names work regardless of case."""
    router = Router()
    
    # Test various casings
    test_cases = [
        "BART: test",
        "Bart: test",
        "bart: test",
        "bArT: test"
    ]
    
    for text in test_cases:
        msg = Message(user_id="u1", text=text)
        agent, reply = router.handle(msg)
        assert agent == "bart", f"Case-insensitive routing failed for: {text}"
    
    print("✓ Case-insensitive routing works")

def test_bukowski_command_variations():
    """Test Bukowski command aliases."""
    router = Router()
    
    # Add history
    msg = Message(user_id="u1", text="Test message")
    router.handle(msg)
    
    # Test "log" alias for "note"
    msg = Message(user_id="u1", text="bukowski: log")
    agent, reply = router.handle(msg)
    assert agent == "bukowski"
    assert reply.startswith("Logged")
    
    # Test "last" alias for "show last"
    msg = Message(user_id="u1", text="bukowski: last")
    agent, reply = router.handle(msg)
    assert agent == "bukowski"
    assert "Last entry:" in reply
    
    # Test "remove last" alias for "delete last"
    msg = Message(user_id="u1", text="bukowski: remove last")
    agent, reply = router.handle(msg)
    assert agent == "bukowski"
    assert reply == "Last entry removed."
    
    print("✓ Bukowski command variations work")

if __name__ == "__main__":
    print("=" * 60)
    print("LPBD INTEGRATION TESTS")
    print("=" * 60)
    print()
    
    test_functions = [
        test_basic_routing,
        test_bukowski_commands,
        test_blanca_pre_router_scan,
        test_crisis_detection,
        test_mute_unmute,
        test_conversation_history,
        test_multi_agent_conversation,
        test_case_insensitive_routing,
        test_bukowski_command_variations,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: ERROR - {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)
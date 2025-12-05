from hypothesis import given, settings
import hypothesis.strategies as st
from time import time
from unittest.mock import patch

from src.router import Router, HistoryPersistence
from src.history import MessageHistory
from src.schemas.message import Message

@given(agent_name=st.sampled_from(["bernie", "jb", "bukowski"]))
@settings(deadline=None)  # Disable deadline - Router init does I/O
def test_mute_unmute_cycle(agent_name):
    """Muting then unmuting should return to original state"""
    router = Router()
    
    # Original state
    original_muted = router.muted_agents.copy()
    
    # Mute
    router.mute_agent(agent_name)
    assert agent_name in router.muted_agents
    
    # Unmute
    router.unmute_agent(agent_name)
    assert agent_name not in router.muted_agents
    assert router.muted_agents == original_muted

@given(text=st.text(min_size=10, max_size=200))
@settings(max_examples=50, deadline=None)
def test_crisis_detection_deterministic(text):
    """Same text should always produce same crisis detection result"""
    router = Router()
    
    result1 = router._detect_crisis(text)
    result2 = router._detect_crisis(text)
    
    assert result1 == result2  # Deterministic

@given(message_text=st.text(min_size=1, max_size=500))
@settings(deadline=None, max_examples=20)
def test_handle_always_returns_tuple(message_text):
    """Any message should return (agent, reply) tuple, never crash"""
    
    # Mock the agent classes' respond methods
    with patch('src.agents.bart.Bart.respond', return_value="Mocked bart"), \
         patch('src.agents.bernie.Bernie.respond', return_value="Mocked bernie"), \
         patch('src.agents.jb.JB.respond', return_value="Mocked jb"), \
         patch('src.agents.blanca.Blanca.respond', return_value="Mocked blanca"), \
         patch('src.agents.hermes.Hermes.respond', return_value="Mocked hermes"):
        
        router = Router()
        
        msg = Message(user_id="test-user", text=message_text, timestamp=time())
        agent, reply = router.handle(msg)
        
        assert isinstance(agent, str)
        assert isinstance(reply, str)
        assert len(agent) > 0
        assert len(reply) > 0

@given(messages=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=20))
@settings(max_examples=20)
def test_history_roundtrip(messages):
    """Saving and loading history should preserve all data"""
    history = MessageHistory()
    persistence = HistoryPersistence()
    user_id = "test-user"
    
    # Add messages using correct method signature
    for msg in messages:
        history.add_turn(
            user_id=user_id,
            user_text=msg,
            reply_text="Test response",
            agent="bart",
            ts=time()
        )
    
    # Save
    persistence.save(history)
    
    # Load fresh
    loaded_history = persistence.load()
    
    # Should have same content
    assert len(loaded_history._history[user_id]) == len(messages)

@given(agent_name=st.sampled_from(["bart", "blanca", "hermes"]))
def test_essential_agents_cannot_be_muted(agent_name):
    """Bart, Blanca, Hermes should never be mutable"""
    router = Router()
    
    # These should fail gracefully or be no-ops
    router.mute_agent(agent_name)
    assert agent_name not in router.muted_agents
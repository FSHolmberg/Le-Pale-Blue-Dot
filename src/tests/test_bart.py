

from src.agents.bart import Bart

def test_empty():
    b = Bart()
    assert b.respond("   ") == "Say something."

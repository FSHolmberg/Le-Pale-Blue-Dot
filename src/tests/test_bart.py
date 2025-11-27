

from src.agents.bart import Bart

def test_empty():
    b = Bart()
    assert b.respond("   ") == "Say something."

def test_short():
    b = Bart()
    assert b.respond("hi") == "That's not much to work with: 'hi'."

def test_question():
    b = Bart()
    assert b.respond("Is this ok?") == "You ask a lot of questions. This one was: 'Is this ok?'"

def test_long():
    b = Bart()
    assert b.respond("hello there friend") == "Alright. I heard: 'hello there friend'"

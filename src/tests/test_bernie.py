
from src.agents.bernie import Bernie


def test_bernie_basic_reflection():
    bernie = Bernie()
    reply = bernie.respond("Bernie: I'm tired of debugging.")
    assert "Bernie:" in reply
    assert "I'm tired of debugging." in reply

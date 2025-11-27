
from src.config.loader import Config

def test_config_loads_prompts():
    cfg = Config()
    bart_prompt = cfg.get_prompt("bart")
    assert isinstance(bart_prompt, str)
    assert len(bart_prompt) > 0

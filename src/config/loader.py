import yaml
from pathlib import Path
from calais_weather import get_environment_for_agent


class Config:
    def __init__(self, path: str = "src/config/prompts.yaml") -> None:
        self.path = Path(path)
        self.data = self._load()

    def _load(self) -> dict:
        with self.path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_prompt(self, agent_name: str) -> str:
        section = self.data.get(agent_name, {})
        base_prompt = section.get("system_prompt", "")
        
        # Inject weather context for Bart
        if agent_name == "bart":
            environment = get_environment_for_agent()
            base_prompt += f"\n\nCURRENT ENVIRONMENT: {environment}\nYou can see this through the window behind the bar. Reference it naturally when relevant—the cold, the wind, the grey light—but don't force it into every response."
        
        return base_prompt
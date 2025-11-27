

import yaml
from pathlib import Path


class Config:
    def __init__(self, path: str = "src/config/prompts.yaml") -> None:
        self.path = Path(path)
        self.data = self._load()

    def _load(self) -> dict:
        with self.path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_prompt(self, agent_name: str) -> str:
        section = self.data.get(agent_name, {})
        return section.get("system_prompt", "")

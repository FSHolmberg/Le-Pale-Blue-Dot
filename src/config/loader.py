import yaml
from pathlib import Path
from src.calais_weather import get_environment_for_agent


class Config:
    def __init__(self, prompts_dir: str = "src/config/prompts") -> None:
        self.prompts_dir = Path(prompts_dir)
        self.data = self._load_all_prompts()

    def _load_all_prompts(self) -> dict:
        """Load all agent prompts from individual YAML files."""
        prompts = {}
        
        # Load each agent's prompt file
        for prompt_file in self.prompts_dir.glob("*.yaml"):
            agent_name = prompt_file.stem  # e.g., "bart" from "bart.yaml"
            with prompt_file.open("r", encoding="utf-8") as f:
                agent_config = yaml.safe_load(f)
                prompts[agent_name] = agent_config
        
        return prompts

    def get_prompt(self, agent_name: str) -> str:
        section = self.data.get(agent_name, {})
        base_prompt = section.get("system_prompt", "")
        
        # Inject weather context for Bart
        if agent_name == "bart":
            environment = get_environment_for_agent()
            base_prompt += f"\n\nCURRENT ENVIRONMENT: {environment}\nYou can see this through the window behind the bar. Reference it naturally when relevant—the cold, the wind, the grey light—but don't force it into every response."
        
        return base_prompt
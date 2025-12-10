import yaml
from pathlib import Path
from src.calais_weather import get_environment_for_agent
from src.calais_tides import get_tide_context_for_agent


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

    def _load_bar_context(self) -> str:
        """Load bar context from YAML file."""
        bar_context_path = Path("src/config/bar_context.yaml")
        
        if not bar_context_path.exists():
            return ""
        
        with bar_context_path.open("r", encoding="utf-8") as f:
            context_data = yaml.safe_load(f)
            return context_data.get("common_knowledge", "")

    def get_prompt(self, agent_name: str) -> str:
        section = self.data.get(agent_name, {})
        base_prompt = section.get("system_prompt", "")
        
        # Inject bar context only for Blanca (she always onboards, triggers cache)
        if agent_name == "blanca":
            bar_context = self._load_bar_context()
            if bar_context:
                base_prompt += f"\n\n{bar_context}"
        
        # Inject weather context for ALL agents (they all see the window)
        environment = get_environment_for_agent()
        base_prompt += f"\n\nCURRENT ENVIRONMENT: {environment}\nVisible through the window. Mention only if genuinely relevant—don't force weather into every response."
        
        # Inject tide context for agents who know tides
        if agent_name in ["bart", "bernie", "jb"]:
            tide_context = get_tide_context_for_agent()
            base_prompt += f"\n\n{tide_context}"
        
        return base_prompt
    
    def get_onboarding_context(self, is_new_user: bool) -> str:
        """Load onboarding context based on user type."""
        onboarding_path = Path("src/config/onboarding_context.yaml")
        
        if not onboarding_path.exists():
            return ""
        
        with onboarding_path.open("r", encoding="utf-8") as f:
            context_data = yaml.safe_load(f)
        
        if is_new_user:
            return context_data.get("new_user_onboarding", "")
        else:
            return context_data.get("recurring_user_onboarding", "")
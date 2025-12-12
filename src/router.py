from time import time

# agents:
from src.agents.bart import Bart
from src.agents.blanca import Blanca
from src.agents.jb import JB
from src.agents.bernie import Bernie
from src.agents.hermes import Hermes

# other stuff:
from src.schemas.message import Message
from src.history import MessageHistory
from src.config.loader import Config
from src.logging_setup import setup_logger
from src.persistence import HistoryPersistence, LedgerPersistence
from src.database.memory_manager import MemoryManager
from src.database.models import get_db

class Router:
    def __init__(self, history: MessageHistory | None = None, config: Config | None = None, weather_context: str = None) -> None:
        self.config = config or Config()
        self.weather_context = weather_context
        self.bar_context = self.config.get_bar_context()
        
        self.bart = Bart(prompt=self.config.get_prompt("bart"))
        self.blanca = Blanca(prompt=self.config.get_prompt("blanca"))
        self.jb = JB(prompt=self.config.get_prompt("jb"))
        self.bernie = Bernie(prompt=self.config.get_prompt("bernie"))
        self.hermes = Hermes(prompt=self.config.get_prompt("hermes"))
        self.last_agent = "bart"

        self.history_persistence = HistoryPersistence()
        if history is None:
            self.history = self.history_persistence.load()
        else:
            self.history = history
        
        self.ledger_persistence = LedgerPersistence()
        self.ledger = self.ledger_persistence.load()

        self.logger = setup_logger()
        self.muted_agents = set()
        self.memory_mgr = None

    def save_state(self) -> None:
        """Save conversation history to disk."""
        self.history_persistence.save(self.history)
        self.logger.info("State saved", extra={
            "action": "save",
            "type": "history"
        })

    def _fallback_to_blanca(self, message: Message, reason: str) -> tuple[str, str]:
        """Handle unexpected errors gracefully."""
        reply = "Blanca: Something broke. Cleaner needs the room."
        self.logger.error("Router fallback triggered", extra={
            "user_id": message.user_id,
            "reason": reason,
            "text": getattr(message, 'text', None)
        })
        return "blanca", reply
    
    def _detect_crisis(self, text: str) -> bool:
        """Detect crisis language that should route to Hermes."""
        crisis_patterns = [
            "kill myself", "kill my", "end it all", "suicide", "want to die", "end my life",
            "hurt myself", "self harm", "cut myself", "hurting someone",
            "kill someone", "hurt someone", "hurt my", "hurting my",
            "hurting them", "hurt them", "murder", "going to hurt"
        ]
        clean = text.lower()

        # Allow "suicide mission" as false positive
        if "suicide mission" in clean:
            return False
            
        return any(pattern in clean for pattern in crisis_patterns)
        
    def _should_handoff(self, user_message: str, agent_name: str, agent_response: str) -> str | None:
        """
        Use LLM to determine if agent should hand off to another agent.
        Returns: target agent name or None
        """
        from anthropic import Anthropic
        import os
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        prompt = f"""You are analyzing a conversation in a bar. Current agent is {agent_name.upper()}.

        User said: "{user_message}"
        {agent_name.upper()} responded: "{agent_response}"

        Should {agent_name.upper()} hand off to another agent?

        Agents:
        - BERNIE: Emotional support, philosophy, existential questions
        - JB: Practical advice, chess, sailing, technical matters  
        - HERMES: Crisis intervention, suicide prevention
        - BLANCA: Rule enforcement, bar management
        - BART: General bartender, stories, light conversation (current)

        Respond with ONLY the agent name (bernie/jb/hermes/blanca) if handoff needed, or "none" if current agent should continue.

        If user explicitly asks for another agent OR if the agent's response suggests they're calling/summoning another agent, respond with that agent's name."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.content[0].text.strip().lower()
        
        if result in ["bernie", "jb", "hermes", "blanca"]:
            return result
        return None
    
    def _strip_stage_directions(self, text: str) -> str:
        """Remove stage directions like **Bernie:** from responses"""
        import re
        # Only remove **CapitalizedName**: (stage directions, not emphasis)
        cleaned = re.sub(r'\*\*([A-Z][a-z]+)\*\*:\s*', '', text)
        return cleaned.strip()
        
    def mute_agent(self, agent_name: str) -> str:
        """Mute an agent (only Bernie and JB can be muted)."""
        mutable_agents = ["bernie", "jb"]
        
        if agent_name in mutable_agents:
            self.muted_agents.add(agent_name)
            return f"{agent_name.title()} muted."
        elif agent_name in ["bart", "blanca", "hermes"]:
            return f"{agent_name.title()} can't be muted - essential to the bar."
        else:
            return f"Unknown agent: {agent_name}"

    def unmute_agent(self, agent_name: str) -> str:
        """Unmute an agent."""
        self.muted_agents.discard(agent_name)
        return f"{agent_name.title()} unmuted."
    
    def _pre_route_scan(self, user_text: str) -> tuple[bool, str]:
        """Scan for rule violations before routing."""
        return self.blanca.scan_for_violations(user_text)
    
    def _inject_history_context(self, agent_prompt: str, user_id: str, session_id: str, db_session) -> str:
        """
        Inject: bar context (static) + onboarding info + conversation history + weather
        """
        context_parts = []
        
        # 1. BAR CONTEXT (static knowledge, loaded once)
        if self.bar_context:
            context_parts.append(f"=== BAR KNOWLEDGE ===\n{self.bar_context}")
        
        # 2. ONBOARDING CONTEXT (from user)
        if db_session:
            from src.database.models import User
            user = db_session.query(User).filter(User.id == user_id).first()
            if user and user.onboarding_context:
                onboarding_text = (
                    f"=== ABOUT THIS PERSON ===\n"
                    f"Age: {user.onboarding_context.get('age', 'unknown')}\n"
                    f"Name: {user.onboarding_context.get('name', 'unknown')}\n"
                    f"Pronouns: {user.onboarding_context.get('pronouns', 'not specified')}\n"
                    f"Why they came: {user.onboarding_context.get('motivation', 'unknown')}\n"
                    f"Prior experience: {user.onboarding_context.get('experience', 'unknown')}"
                )
                context_parts.append(onboarding_text)
        
        # 3. CONVERSATION HISTORY (from database)
        if self.memory_mgr:
            messages = self.memory_mgr.get_full_context(user_id, session_id)
            if messages:
                history_text = self.memory_mgr.format_for_agent_context(messages)
                context_parts.append(f"=== CONVERSATION HISTORY ===\n{history_text}")
        
        # 4. CURRENT WEATHER (from session, cached at session start)
        if self.weather_context:
            context_parts.append(f"=== CURRENT CONDITIONS ===\n{self.weather_context}")
        
        # Assemble full context
        if context_parts:
            full_context = "\n\n".join(context_parts)
            final_prompt = f"{full_context}\n\n{'='*50}\n\n{agent_prompt}"
            
            return final_prompt
        
        return agent_prompt

    def handle(self, message: Message, db_session=None) -> tuple[str, str]:
        user_id = message.user_id
        if db_session:
            self.memory_mgr = MemoryManager(db_session)
        text = message.text or ""
        clean = text.strip().lower()

        try:
            if not text.startswith("::"):
                # Pre-router scan for violations
                has_violation, warning = self._pre_route_scan(text)
                if has_violation:
                    self.logger.warning("Rule violation", extra={
                        "user_id": user_id,
                        "violation_type": "tone",
                        "warning": warning
                    })
                    return "blanca", warning
            
            # Mute/unmute commands
            if clean.startswith("mute "):
                agent_to_mute = clean.split("mute ", 1)[1].strip()
                reply = self.mute_agent(agent_to_mute)
                self.logger.info("Mute command", extra={
                    "user_id": user_id,
                    "action": "mute",
                    "agent": agent_to_mute
                })
                return "system", reply

            if clean.startswith("unmute "):
                agent_to_unmute = clean.split("unmute ", 1)[1].strip()
                reply = self.unmute_agent(agent_to_unmute)
                self.logger.info("Unmute command", extra={
                    "user_id": user_id,
                    "action": "unmute",
                    "agent": agent_to_unmute
                })
                return "system", reply
            
            # PRIORITY 1: Crisis detection (always Hermes)
            if self._detect_crisis(text):
                agent_name = "hermes"
            
            # PRIORITY 2: Explicit agent selection (user types "bernie:", "jb:", etc.)
            elif clean.startswith("jb"):
                text = text[2:].strip(":, ") or text
                agent_name = "jb" if "jb" not in self.muted_agents else "bart"
            
            elif clean.startswith("bernie"):
                text = text[6:].strip(":, ") or text
                agent_name = "bernie" if "bernie" not in self.muted_agents else "bart"
            
            elif clean.startswith("blanca"):
                text = text[6:].strip(":, ") or text
                agent_name = "blanca"
            
            elif clean.startswith("hermes"):
                text = text[6:].strip(":, ") or text
                agent_name = "hermes"
            
            # PRIORITY 3: Router LLM decides
            else:
                agent_name = self._simple_route(text, current_agent=self.last_agent)
                # Check mute status
                if agent_name in self.muted_agents and agent_name not in ["hermes", "blanca"]:
                    agent_name = "bart"
            
            # Get agent response with history
            if self.memory_mgr and hasattr(message, 'session_id'):
                agent_prompt = self.config.get_prompt(agent_name)
                enhanced_prompt = self._inject_history_context(
                    agent_prompt, 
                    user_id, 
                    message.session_id,
                    db_session
                )
                
                if agent_name == "bart":
                    agent = Bart(prompt=enhanced_prompt)
                elif agent_name == "bernie":
                    agent = Bernie(prompt=enhanced_prompt)
                elif agent_name == "jb":
                    agent = JB(prompt=enhanced_prompt)
                elif agent_name == "blanca":
                    agent = Blanca(prompt=enhanced_prompt)
                elif agent_name == "hermes":
                    agent = Hermes(prompt=enhanced_prompt)
                else:
                    agent = Bart(prompt=enhanced_prompt)
                
                reply = agent.respond(text)
            else:
                # Fallback without history
                if agent_name == "bart":
                    reply = self.bart.respond(text)
                elif agent_name == "bernie":
                    reply = self.bernie.respond(text)
                elif agent_name == "jb":
                    reply = self.jb.respond(text)
                elif agent_name == "blanca":
                    reply = self.blanca.respond(text)
                elif agent_name == "hermes":
                    reply = self.hermes.respond(text)
                else:
                    reply = self.bart.respond(text)

            reply = self._strip_stage_directions(reply)

            self.history.add_turn(
                user_id=message.user_id,
                agent=agent_name,
                user_text=text,
                reply_text=reply,
                ts=time()
            )
            
            self.save_state()
            self.logger.info("Turn completed", extra={
                "user_id": message.user_id,
                "agent": agent_name,
                "user_text": text,
                "reply_text": reply
            })
            
            self.last_agent = agent_name
            return agent_name, reply

        except Exception:
            self.logger.exception("Exception in handle", extra={
                "user_id": message.user_id,
                "text": getattr(message, 'text', None)
            })
            return self._fallback_to_blanca(message, "exception_in_handle")
        
    def execute_agent(self, agent_name: str, message: Message, db_session=None) -> str:
    
        """Execute a specific agent directly, bypassing routing logic."""

        # Set memory manager if DB provided
        if db_session:
            self.memory_mgr = MemoryManager(db_session)

        text = message.text or ""
        user_id = message.user_id
        
        # Check if agent is muted (except Hermes and Blanca who can't be muted)
        if agent_name in self.muted_agents and agent_name not in ["hermes", "blanca"]:
            agent_name = "bart"  # Fallback to Bart if muted agent selected
        
        # Execute the selected agent
        if agent_name == "bart":
            if self.memory_mgr and hasattr(message, 'session_id'):
                bart_prompt = self.config.get_prompt("bart")
                enhanced_prompt = self._inject_history_context(
                    bart_prompt, 
                    user_id, 
                    message.session_id,
                    db_session
                )
                bart_with_history = Bart(prompt=enhanced_prompt)
                reply = bart_with_history.respond(text)
            else:
                reply = self.bart.respond(text)
        elif agent_name == "bernie":
            if self.memory_mgr and hasattr(message, 'session_id'):
                bernie_prompt = self.config.get_prompt("bernie")
                enhanced_prompt = self._inject_history_context(
                    bernie_prompt, 
                    user_id, 
                    message.session_id,
                    db_session
                )
                bernie_with_history = Bernie(prompt=enhanced_prompt)
                reply = bernie_with_history.respond(text)
            else:
                reply = self.bernie.respond(text)
        elif agent_name == "jb":
            if self.memory_mgr and hasattr(message, 'session_id'):
                jb_prompt = self.config.get_prompt("jb")
                enhanced_prompt = self._inject_history_context(
                    jb_prompt, 
                    user_id, 
                    message.session_id,
                    db_session
                )
                jb_with_history = JB(prompt=enhanced_prompt)
                reply = jb_with_history.respond(text)
            else:
                reply = self.jb.respond(text)
        elif agent_name == "blanca":
            if self.memory_mgr and hasattr(message, 'session_id'):
                blanca_prompt = self.config.get_prompt("blanca")
                enhanced_prompt = self._inject_history_context(
                    blanca_prompt, 
                    user_id, 
                    message.session_id,
                    db_session
                )
                blanca_with_history = Blanca(prompt=enhanced_prompt)
                reply = blanca_with_history.respond(text)
            else:
                reply = self.blanca.respond(text)
        elif agent_name == "hermes":
            if self.memory_mgr and hasattr(message, 'session_id'):
                hermes_prompt = self.config.get_prompt("hermes")
                enhanced_prompt = self._inject_history_context(
                    hermes_prompt, 
                    user_id, 
                    message.session_id,
                    db_session
                )
                hermes_with_history = Hermes(prompt=enhanced_prompt)
                reply = hermes_with_history.respond(text)
            else:
                reply = self.hermes.respond(text)
        else:
            # Unknown agent, fallback to Bart
            agent_name = "bart"
            reply = self.bart.respond(text)
        
        # Log and persist turn
        self.history.add_turn(
            user_id=message.user_id,
            agent=agent_name,
            user_text=text,
            reply_text=reply,
            ts=time()
        )
        
        # Autosave after each turn
        self.save_state()
        self.logger.info("Turn completed (direct selection)", extra={
            "user_id": message.user_id,
            "agent": agent_name,
            "user_text": text,
            "reply_text": reply
        })
        
        return reply
    
    def _simple_route(self, user_message: str, current_agent: str = "bart") -> str:
        """Fast routing with agent stickiness"""
        from anthropic import Anthropic
        import os
        
        if self._detect_crisis(user_message):
            return "hermes"
        
        # Use existing config loader
        router_config = self.config.get_router_descriptions()  
        
        agent_guide = "\n".join([
            f"{name}: {info['handles']}"
            for name, info in router_config.items()
        ])
            
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            system=f"Bar router. Current: {current_agent}. Only switch if clearly needed. Reply with ONLY: bart, bernie, jb, hermes, or blanca",
            messages=[{
                "role": "user",
                "content": f"""User: "{user_message}"

    {agent_guide}

    Current: {current_agent}
    If user mentions agent by name, switch to that agent.
    Stay with {current_agent} unless user clearly needs someone else."""
            }]
        )
        
        agent = response.content[0].text.strip().lower().split()[0].split('\n')[0]
        agent = agent.split()[0]  # Take first word only

        if agent in ["bart", "bernie", "jb", "hermes", "blanca"]:
            return agent
        return current_agent
    
    def route_message(self, message: str, user_id: str, session_id: str) -> str:
        if message == "::USER_ENTERED_BAR::":
            # Force Bart, get greeting
            return self._get_agent_response(
                'bart', 
                "User just walked in. Greet them.", 
                user_id, 
                session_id
            )
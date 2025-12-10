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
    def __init__(self, history: MessageHistory | None = None, config: Config | None = None) -> None:
        self.config = config or Config()
        self.bart = Bart(prompt=self.config.get_prompt("bart"))
        self.blanca = Blanca(prompt=self.config.get_prompt("blanca"))
        self.jb = JB(prompt=self.config.get_prompt("jb"))
        self.bernie = Bernie(prompt=self.config.get_prompt("bernie"))
        self.hermes = Hermes(prompt=self.config.get_prompt("hermes"))

        self.history_persistence = HistoryPersistence()
        # Load existing history if available, otherwise use provided or create new
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

    def _detect_handoff(self, agent_response: str) -> str | None:
        """
        Detect if agent is handing off to another agent.
        Returns: agent_name to hand off to, or None
        """
        response_lower = agent_response.lower()
        
        # More flexible handoff patterns
        handoff_patterns = {
            "bernie": [
                "let me get bernie",
                "i'll get bernie",
                "bernie should",
                "talk to bernie",
                "bernie can help",
                "bernie has a",
                "bernie?",  # When calling Bernie
                "bernie's better",
                "asking for you" # Stage direction pattern
            ],
            "jb": [
                "let me get jb",
                "i'll get jb",
                "jb should",
                "talk to jb",
                "jb can help",
                "jb?",
                "jb's better"
            ],
            "hermes": [
                "let me get hermes",
                "i'll get hermes",
                "hermes should",
                "talk to hermes",
                "hermes can help",
                "hermes?"
            ],
            "blanca": [
                "let me get blanca",
                "i'll get blanca",
                "blanca should",
                "talk to blanca",
                "blanca?"
            ]
        }
        
        # Also detect stage directions (fallback)
        # Pattern: **AgentName:** or **AgentName**
        import re
        stage_direction = re.search(r'\*\*([a-z]+)\*\*', response_lower)
        if stage_direction:
            detected_agent = stage_direction.group(1)
            if detected_agent in ["bernie", "jb", "hermes", "blanca"]:
                return detected_agent
        
        for target_agent, patterns in handoff_patterns.items():
            if any(pattern in response_lower for pattern in patterns):
                return target_agent
        
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
    
    def _inject_history_context(self, agent_prompt: str, user_id: str, session_id: str) -> str:
        """
        Inject conversation history into agent prompt.
        Returns: Modified prompt with history context prepended.
        """
        if not self.memory_mgr:
            return agent_prompt  # No DB session available, skip history
        
        # Get full context (cold + hot storage)
        messages = self.memory_mgr.get_full_context(user_id, session_id)
        
        if not messages:
            return agent_prompt  # No history yet
        
        # Format for context injection
        history_context = self.memory_mgr.format_for_agent_context(messages)
        
        # Inject BEFORE the main agent instructions
        return f"{history_context}\n\n{agent_prompt}"

    def handle(self, message: Message, db_session=None) -> tuple[str, str]:
        user_id = message.user_id
        if db_session:
            self.memory_mgr = MemoryManager(db_session)
        text = message.text or ""
        clean = text.strip().lower()

        try:
            # Pre-router scan for violations (CAPS, empty, etc.)
            has_violation, warning = self._pre_route_scan(text)
            if has_violation:
                self.logger.warning("Rule violation", extra={
                    "user_id": user_id,
                    "violation_type": "tone",
                    "warning": warning
                })
                return "blanca", warning
            
            # Check for mute/unmute commands
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
            
            # Check for crisis (route to Hermes - can't be muted)
            if self._detect_crisis(text):
                agent_name = "hermes"
                
                if self.memory_mgr and hasattr(message, 'session_id'):
                    hermes_prompt = self.config.get_prompt("hermes")
                    enhanced_prompt = self._inject_history_context(
                        hermes_prompt, 
                        user_id, 
                        message.session_id
                    )
                    hermes_with_history = Hermes(prompt=enhanced_prompt)
                    reply = hermes_with_history.respond(text)
                else:
                    reply = self.hermes.respond(text)

            # Explicit agent routing (with mute checks where applicable)
            elif clean.startswith("jb"):
                user_message = text[2:].strip(":, ") or text
                
                if "jb" in self.muted_agents:
                    agent_name = "bart"
                    reply = self.bart.respond(user_message)
                else:
                    agent_name = "jb"
                    
                    if self.memory_mgr and hasattr(message, 'session_id'):
                        jb_prompt = self.config.get_prompt("jb")
                        enhanced_prompt = self._inject_history_context(
                            jb_prompt, 
                            user_id, 
                            message.session_id
                        )
                        jb_with_history = JB(prompt=enhanced_prompt)
                        reply = jb_with_history.respond(user_message)
                    else:
                        reply = self.jb.respond(user_message)

            elif clean.startswith("bernie"):
                user_message = text[6:].strip(":, ") or text
                
                if "bernie" in self.muted_agents:
                    agent_name = "bart"
                    reply = self.bart.respond(user_message)
                else:
                    agent_name = "bernie"
                    
                    if self.memory_mgr and hasattr(message, 'session_id'):
                        bernie_prompt = self.config.get_prompt("bernie")
                        enhanced_prompt = self._inject_history_context(
                            bernie_prompt, 
                            user_id, 
                            message.session_id
                        )
                        bernie_with_history = Bernie(prompt=enhanced_prompt)
                        reply = bernie_with_history.respond(user_message)
                    else:
                        reply = self.bernie.respond(user_message)

            elif clean.startswith("blanca"):
                user_message = text[6:].strip(":, ") or text
                agent_name = "blanca"
                
                if self.memory_mgr and hasattr(message, 'session_id'):
                    blanca_prompt = self.config.get_prompt("blanca")
                    enhanced_prompt = self._inject_history_context(
                        blanca_prompt, 
                        user_id, 
                        message.session_id
                    )
                    blanca_with_history = Blanca(prompt=enhanced_prompt)
                    reply = blanca_with_history.respond(user_message)
                else:
                    reply = self.blanca.respond(user_message)

            elif clean.startswith("hermes"):
                user_message = text[6:].strip(":, ") or text
                agent_name = "hermes"
                
                if self.memory_mgr and hasattr(message, 'session_id'):
                    hermes_prompt = self.config.get_prompt("hermes")
                    enhanced_prompt = self._inject_history_context(
                        hermes_prompt, 
                        user_id, 
                        message.session_id
                    )
                    hermes_with_history = Hermes(prompt=enhanced_prompt)
                    reply = hermes_with_history.respond(user_message)
                else:
                    reply = self.hermes.respond(user_message)

            # Default to Bart
            else:
                agent_name = "bart"

                if self.memory_mgr and hasattr(message, 'session_id'):
                    bart_prompt = self.config.get_prompt("bart")
                    enhanced_prompt = self._inject_history_context(
                        bart_prompt, 
                        user_id, 
                        message.session_id
                    )
                    bart_with_history = Bart(prompt=enhanced_prompt)
                    reply = bart_with_history.respond(text)
                else:
                    reply = self.bart.respond(text)

            # Strip stage directions and detect handoff
            reply = self._strip_stage_directions(reply)
            handoff_target = self._detect_handoff(reply)

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
            self.logger.info("Turn completed", extra={
                "user_id": message.user_id,
                "agent": agent_name,
                "user_text": text,
                "reply_text": reply
            })
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
                    message.session_id
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
                    message.session_id
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
                    message.session_id
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
                    message.session_id
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
                    message.session_id
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
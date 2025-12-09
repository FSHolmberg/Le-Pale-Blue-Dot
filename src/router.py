from time import time

# agents:
from src.agents.bart import Bart
from src.agents.blanca import Blanca
from src.agents.jb import JB
from src.agents.bernie import Bernie
from src.agents.hermes import Hermes
from src.agents import bukowski

# other stuff:
from src.schemas.message import Message
from src.history import MessageHistory
from src.config.loader import Config
from src.logging_setup import setup_logger
from src.agents.bukowski_ledger import BukowskiLedger
from src.persistence import HistoryPersistence, LedgerPersistence


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

    def save_state(self) -> None:
        """Save conversation history to disk."""
        self.history_persistence.save(self.history)
        self.logger.info("State saved", extra={
            "action": "save",
            "type": "history"
        })

    def save_ledger(self) -> None:
        """Save Bukowski's ledger to disk."""
        self.ledger_persistence.save(self.ledger)
        self.logger.info("Ledger saved", extra={
            "action": "save",
            "type": "ledger"
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
    
    def mute_agent(self, agent_name: str) -> str:
        """Mute an agent (only Bernie, JB, and Bukowski can be muted)."""
        mutable_agents = ["bernie", "jb", "bukowski"]
        
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

    def handle(self, message: Message) -> tuple[str, str]:
        user_id = message.user_id
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
            
            # Debug command
            if clean == "history":
                recent = self.history.get_recent(user_id, limit=5)
                if not recent:
                    reply = "No history found."
                else:
                    reply = f"Last {len(recent)} turns:\n"
                    for turn in recent:
                        reply += f"- {turn.agent}: {turn.user_text[:50]}...\n"
                return "system", reply
            
            # Check for crisis (route to Hermes - can't be muted)
            if self._detect_crisis(text):
                agent_name = "hermes"
                reply = self.hermes.respond(text)

            # Explicit agent routing (with mute checks where applicable)
            elif clean.startswith("jb"):
                user_message = text[2:].strip(":, ") or text
                
                if "jb" in self.muted_agents:
                    agent_name = "bart"
                    reply = self.bart.respond(user_message)
                else:
                    agent_name = "jb"
                    reply = self.jb.respond(user_message)

            elif clean.startswith("bernie"):
                user_message = text[6:].strip(":, ") or text
                
                if "bernie" in self.muted_agents:
                    agent_name = "bart"
                    reply = self.bart.respond(user_message)
                else:
                    agent_name = "bernie"
                    reply = self.bernie.respond(user_message)

            elif clean.startswith("blanca"):
                user_message = text[6:].strip(":, ") or text
                agent_name = "blanca"
                reply = self.blanca.respond(user_message)

            elif clean.startswith("bukowski"):
                agent_name = "bukowski"
                reply = bukowski.handle_bukowski(
                    user_id=user_id,
                    raw_text=text,
                    history=self.history,
                    ledger=self.ledger,
                    now=time()
                )
                self.save_ledger()

            elif clean.startswith("hermes"):
                user_message = text[6:].strip(":, ") or text
                agent_name = "hermes"
                reply = self.hermes.respond(user_message)

            # Default to Bart
            else:
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
        
    def execute_agent(self, agent_name: str, message: Message) -> str:
        """Execute a specific agent directly, bypassing routing logic."""
        text = message.text or ""
        user_id = message.user_id
        
        # Check if agent is muted (except Hermes and Blanca who can't be muted)
        if agent_name in self.muted_agents and agent_name not in ["hermes", "blanca"]:
            agent_name = "bart"  # Fallback to Bart if muted agent selected
        
        # Execute the selected agent
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
        elif agent_name == "bukowski":
            reply = bukowski.handle_bukowski(
                user_id=user_id,
                raw_text=text,
                history=self.history,
                ledger=self.ledger,
                now=time()
            )
            self.save_ledger()
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
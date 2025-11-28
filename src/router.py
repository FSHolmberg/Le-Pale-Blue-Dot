from time import time

#agents:
from src.agents.bart import Bart
from src.agents.blanca import Blanca
from src.agents.jb import JB
from src.agents.bernie import Bernie
from src.agents.hermes import Hermes
from src.agents import bukowski

#other stuff:
from src.schemas.message import Message
from src.history import MessageHistory
from src.config.loader import Config
from src.logging_setup import setup_logger
from src.agents.bukowski_ledger import BukowskiLedger


class Router:
    def __init__(self, history: MessageHistory | None = None, config: Config | None = None) -> None:
        self.config = config or Config()
        self.bart = Bart(prompt=self.config.get_prompt("bart"))
        self.blanca = Blanca(prompt=self.config.get_prompt("blanca"))
        self.jb = JB(prompt=self.config.get_prompt("jb"))
        self.bernie = Bernie(prompt=self.config.get_prompt("bernie"))
        self.hermes = Hermes(prompt=self.config.get_prompt("hermes"))
        self.history = history or MessageHistory()
        self.ledger = BukowskiLedger()
        self.logger = setup_logger()

    def _fallback_to_blanca(self, message: Message, reason: str) -> tuple[str, str]:
        reply = "Blanca: Something broke. Cleaner needs the room."
        self.logger.error(
            f"router_fallback user={message.user_id} reason={reason} text={getattr(message, 'text', None)!r}")
        return "blanca", reply


    def handle(self, message: Message) -> tuple[str, str]:
        user_id = message.user_id
        text = message.text or ""
        clean = text.strip().lower()

        try:
            if not text or text.strip() == "":
                return self._fallback_to_blanca(message, "empty_message")

            if text.isupper() and text.strip() != "":
                agent_name = "blanca"
                reply = self.blanca.respond(text)

            elif clean == "jb" or clean.startswith("jb,") or clean.startswith("jb "):
                agent_name = "jb"
                # Strip "jb" prefix if present
                if clean != "jb":
                    user_message = text.split("jb", 1)[1].strip(",: ")
                else:
                    user_message = text
                reply = self.jb.respond(user_message)

            elif clean == "bernie" or clean.startswith("bernie,") or clean.startswith("bernie "):
                agent_name = "bernie"
                # Strip "bernie:" or "bernie," prefix
                if clean != "bernie":
                    user_message = text.split("bernie", 1)[1].strip(":, ")
                else: user_message = text
                reply = self.bernie.respond(user_message)

            elif clean.startswith("bukowski"):
                agent_name = "bukowski"
                reply = bukowski.handle_bukowski(
                    user_id=user_id,
                    raw_text=text,
                    history=self.history,
                    ledger=self.ledger,
                    now=time())

            elif clean.startswith("hermes"):
                agent_name = "hermes"
                reply = self.hermes.respond(text)

            else:
                agent_name = "bart"
                reply = self.bart.respond(text)

            #agent reply logged separately
            self.history.add_turn(
                user_id=message.user_id,
                agent=agent_name,
                user_text=text,
                reply_text=reply,
                ts=time())

            self.logger.info(f"user={message.user_id} agent={agent_name} text={text!r} reply={reply!r}")

            return agent_name, reply

        except Exception:
            self.logger.exception(
                f"router_handle_exception user={message.user_id} text={getattr(message, 'text', None)!r}")
            
            return self._fallback_to_blanca(message, "exception_in_handle")
    
     


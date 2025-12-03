import json
from pathlib import Path
from src.history import MessageHistory
from src.agents.bukowski_ledger import BukowskiLedger, LedgerEntry


class HistoryPersistence:
    """Save and load conversation history to/from JSON."""
    
    def __init__(self, filepath: str = "data/history.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)  # Create data/ if needed
    
    def save(self, history: MessageHistory) -> None:
        """Save history to JSON file."""
        # Convert internal structure to JSON-friendly format
        data = {}
        for user_id, turns_deque in history._history.items():
            # Convert deque to list of dicts
            turns_list = [
                {
                    "user_id": turn.user_id,
                    "agent": turn.agent,
                    "user_text": turn.user_text,
                    "reply_text": turn.reply_text,
                    "timestamp": turn.timestamp
                }
                for turn in turns_deque
            ]
            data[user_id] = turns_list
        
        # Write to file
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def load(self) -> MessageHistory:
        """Load history from JSON file."""
        if not self.filepath.exists():
            return MessageHistory()  # Return empty history if file doesn't exist
        
        with open(self.filepath, "r") as f:
            data = json.load(f)
        
        # Reconstruct MessageHistory
        history = MessageHistory()
        for user_id, turns_list in data.items():
            for turn_dict in turns_list:
                history.add_turn(
                    user_id=turn_dict["user_id"],
                    agent=turn_dict["agent"],
                    user_text=turn_dict["user_text"],
                    reply_text=turn_dict["reply_text"],
                    ts=turn_dict["timestamp"]
                )
        
        return history
    
class LedgerPersistence:
    """Save and load Bukowski's ledger to/from JSON."""
    
    def __init__(self, filepath: str = "data/ledger.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
    
    def save(self, ledger: BukowskiLedger) -> None:
        """Save ledger to JSON file."""
        data = [
            {
                "user_id": entry.user_id,
                "agent": entry.agent,
                "text": entry.text,
                "ts": entry.ts
            }
            for entry in ledger._entries
        ]
        
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def load(self) -> BukowskiLedger:
        """Load ledger from JSON file."""
        if not self.filepath.exists():
            return BukowskiLedger()
        
        with open(self.filepath, "r") as f:
            data = json.load(f)
        
        ledger = BukowskiLedger()
        for entry_dict in data:
            ledger.log(LedgerEntry(
                user_id=entry_dict["user_id"],
                agent=entry_dict["agent"],
                text=entry_dict["text"],
                ts=entry_dict["ts"]
            ))
        
        return ledger
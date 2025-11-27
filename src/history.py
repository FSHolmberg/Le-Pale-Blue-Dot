

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from time import time
from typing import Deque, Dict, List


@dataclass
class DialogueTurn:
    user_id: str
    agent: str
    user_text: str
    reply_text: str
    timestamp: float 


class MessageHistory:

    def __init__(self, max_turns_per_user: int = 50) -> None:
        self._max_turns = max_turns_per_user
        self._history: Dict[str, Deque[DialogueTurn]] = defaultdict(
            lambda: deque(maxlen=self._max_turns))

    def add_turn(
        self,
        *,
        user_id: str,
        agent: str,
        user_text: str,
        reply_text: str,
        ts: float | None = None,
    ) -> None:

        turn = DialogueTurn(
            user_id=user_id,
            agent=agent,
            user_text=user_text,
            reply_text=reply_text,
            timestamp=ts if ts is not None else time())
        
        self._history[user_id].append(turn)

    def get_recent(self, user_id: str, limit: int | None = None) -> List[DialogueTurn]:
        turns = list(self._history[user_id])
        if limit is None or limit >= len(turns):
            return turns
        return turns[-limit:]

    def clear_user(self, user_id: str) -> None:
        self._history.pop(user_id, None)

    def clear_all(self) -> None:
        self._history.clear()

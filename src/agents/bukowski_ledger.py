from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LedgerEntry:
    user_id: str
    agent: str
    text: str
    ts: float


class BukowskiLedger:
    def __init__(self) -> None:
        self._entries: List[LedgerEntry] = []

    def log(self, entry: LedgerEntry | str) -> None:
        if isinstance(entry, LedgerEntry):
            self._entries.append(entry)
        else:
            self._entries.append(
                LedgerEntry(
                    user_id="",
                    agent="manual",
                    text=str(entry),
                    ts=0.0))

    def get_last(self, n: Optional[int] = None) -> List[LedgerEntry]:
        if n is not None:
            if n <= 0:
                return []
            return self._entries[-n:]

        result = list(self._entries)
        self._entries.clear()
        return result

    def delete_last(self) -> bool:
        if not self._entries:
            return False
        self._entries.pop()
        return True

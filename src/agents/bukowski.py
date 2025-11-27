

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from src.history import MessageHistory, DialogueTurn
from src.agents.bukowski_ledger import BukowskiLedger, LedgerEntry


BukowskiCommand = Literal["note", "show_last", "delete_last", "help", "unknown",]


def parse_bukowski_command(text: str) -> BukowskiCommand:
    lowered = text.strip().lower()

    if lowered.startswith("bukowski:"):
        lowered = lowered[len("bukowski:"):].strip()

    if not lowered:
        return "help"

    if lowered.startswith(("note", "log", "write")):
        return "note"

    if lowered.startswith(("show last", "last", "show note")):
        return "show_last"

    if lowered.startswith(("delete last", "erase last", "remove last")):
        return "delete_last"

    if lowered.startswith("help"):
        return "help"

    return "unknown"


def _summarise_history(turns: Sequence[DialogueTurn]) -> str:
    if not turns:
        return "No recent conversation. Empty state logged."

    tail = turns[-6:]

    lines: list[str] = []
    for t in tail:
        user = (t.user_text or "").replace("\n", " ").strip()
        reply = (t.reply_text or "").replace("\n", " ").strip()

        snippet_parts = []
        if user:
            snippet_parts.append(f"U: {user}")
        if reply:
            snippet_parts.append(f"{t.agent}: {reply}")

        if not snippet_parts:
            continue

        snippet = " ".join(snippet_parts)
        if len(snippet) > 160:
            snippet = snippet[:157].rstrip() + "..."
        lines.append(snippet)

    if not lines:
        return "No recent conversation. Empty state logged."

    return " | ".join(lines)


def handle_bukowski(
    user_id: str,
    raw_text: str,
    history: MessageHistory,
    ledger: BukowskiLedger,
    now: float,
) -> str:
    cmd = parse_bukowski_command(raw_text)

    if cmd == "help":
        return (
            "I log and retrieve.\n"
            "- 'bukowski: note' — summarise recent conversation and store it.\n"
            "- 'bukowski: show last' — show your latest entry.\n"
            "- 'bukowski: delete last' — remove the latest entry."
        )

    if cmd == "note":
        recent_turns = history.get_recent(user_id=user_id, limit=10)
        summary = _summarise_history(recent_turns)

        try:
            entry = LedgerEntry(
                user_id=user_id,
                agent="bukowski",
                text=summary,
                ts=now,
            )
            ledger.log(entry)
        except Exception:
            return "Something jammed. Try again."

        return "Logged. One new entry in your ledger."

    if cmd == "show_last":
        try:
            last_list = ledger.get_last(1)  # non-consuming single last entry
        except Exception:
            return "Something jammed. Try again."

        if not last_list:
            return "No entries. Ledger is clean."

        last = last_list[0]
        return f"Last entry:\n{last.text}"

    if cmd == "delete_last":
        try:
            deleted = ledger.delete_last()
        except Exception:
            return "Something jammed. Try again."

        if not deleted:
            return "Nothing to delete."
        return "Last entry removed."

    return (
        "Unclear instruction.\n"
        "Use:\n"
        "- 'bukowski: note'\n"
        "- 'bukowski: show last'\n"
        "- 'bukowski: delete last'\n"
        "- 'bukowski: help'"
    )



from pydantic import BaseModel


class Message:
    def __init__(self, user_id: str, text: str, session_id: str = None):
        self.user_id = user_id
        self.text = text
        self.session_id = session_id or "default_session"
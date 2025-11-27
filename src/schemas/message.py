

from pydantic import BaseModel


class Message(BaseModel):
    user_id: str
    text: str
    timestamp: float

# Data models and schemas

from pydantic import BaseModel
from typing import Optional

class Message(BaseModel):
    session_id: str
    message: str

class Lead(BaseModel):
    session_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    interest: Optional[str] = None
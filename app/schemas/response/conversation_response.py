"""Pydantic response schema for conversation listings."""
from pydantic import BaseModel


class ConversationOut(BaseModel):
    thread_id: str
    title: str
    updated_at: str

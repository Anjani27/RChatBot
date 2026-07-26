"""Pydantic request schemas for chat and conversations."""
from pydantic import BaseModel
from typing import Optional


class ChatPayload(BaseModel):
    thread_id: Optional[str] = None
    message: str


class RenamePayload(BaseModel):
    title: str

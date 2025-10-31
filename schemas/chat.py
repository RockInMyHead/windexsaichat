"""
Chat-related Pydantic schemas
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class MessageBase(BaseModel):
    content: str
    role: str  # "user" or "assistant"


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    title: Optional[str] = None
    model: str = "gpt-4o-mini"


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = []

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-4o-mini"
    conversation_id: Optional[int] = None
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    message_id: int


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    max_tokens: int
    capabilities: List[str]

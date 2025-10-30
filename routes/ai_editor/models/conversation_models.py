from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, validator


class ConversationSummary(BaseModel):
    id: int
    title: str
    date: str
    message_count: int


class ConversationsListResponse(BaseModel):
    conversations: List[ConversationSummary]


class MessageInfo(BaseModel):
    role: str
    content: str
    timestamp: str

    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'assistant', 'system']:
            raise ValueError('role must be user, assistant, or system')
        return v


class ConversationDetail(BaseModel):
    id: int
    title: str
    created_at: str
    messages: List[MessageInfo]


class ConversationDetailResponse(BaseModel):
    conversation: ConversationDetail


class DownloadResponse(BaseModel):
    url: str
    filename: str


class PreviewResponse(BaseModel):
    url: str
    content_type: str


class StatusResponse(BaseModel):
    status: str
    uptime: float
    total_conversations: int
    total_messages: int

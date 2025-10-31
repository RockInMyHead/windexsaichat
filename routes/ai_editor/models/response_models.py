from pydantic import BaseModel


class AIEditorResponse(BaseModel):
    content: str
    conversation_id: int
    status: str
    timestamp: str


class LLMThought(BaseModel):
    icon: str
    text: str
    timestamp: str


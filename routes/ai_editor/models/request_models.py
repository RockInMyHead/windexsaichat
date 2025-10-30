from typing import Dict, List, Optional
from pydantic import BaseModel, validator


class AIEditorRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str = "gpt-4o-mini"
    conversation_id: Optional[int] = None
    mode: str = "lite"  # "lite" or "pro"
    use_two_stage: bool = True  # Use two-stage LLM system

    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError('messages cannot be empty')
        return v


class ElementEditRequest(BaseModel):
    element_type: str
    current_text: str
    edit_instruction: str
    html_content: str

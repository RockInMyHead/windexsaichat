from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from routes.auth import get_current_user, User
from utils.ai_helpers import generate_ai_response

router = APIRouter()

# In-memory storage for conversations
conversations = {}

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    model: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    response: str
    conversation_id: str
    model_used: str
    timestamp: str

@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Process chat message and return AI response"""
    
    # Generate conversation ID if not provided
    if not request.conversation_id:
        conversation_id = f"conv_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        conversation_id = request.conversation_id
    
    # Initialize conversation if new
    if conversation_id not in conversations:
        conversations[conversation_id] = {
            "id": conversation_id,
            "title": "Новый чат",
            "timestamp": datetime.now().isoformat(),
            "messages": []
        }
    
    # Add user message
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.now().isoformat()
    )
    conversations[conversation_id]["messages"].append(user_message)
    
    # Generate AI response
    ai_response = generate_ai_response(request.message, request.model)
    
    # Add AI response
    ai_message = ChatMessage(
        role="assistant",
        content=ai_response,
        timestamp=datetime.now().isoformat()
    )
    conversations[conversation_id]["messages"].append(ai_message)
    
    # Update conversation title based on first user message
    if len(conversations[conversation_id]["messages"]) == 2:  # First exchange
        title = request.message[:50] + "..." if len(request.message) > 50 else request.message
        conversations[conversation_id]["title"] = title
    
    return ChatResponse(
        response=ai_response,
        conversation_id=conversation_id,
        model_used=request.model,
        timestamp=datetime.now().isoformat()
    )

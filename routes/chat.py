from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from routes.auth import get_current_user, User
from utils.openai_client import generate_response, format_messages_for_openai
from database import get_db, Conversation as DBConversation, Message as DBMessage

router = APIRouter()

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    model: str
    conversation_id: Optional[int] = None

class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    response: str
    conversation_id: int
    model_used: str
    timestamp: str

@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Process chat message and return AI response"""
    
    # Generate conversation ID if not provided
    if not request.conversation_id:
        # Create new conversation
        conversation = DBConversation(
            title="Новый чат",
            user_id=current_user.id
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id
    else:
        conversation_id = request.conversation_id
        # Verify conversation belongs to user
        conversation = db.query(DBConversation).filter(
            DBConversation.id == conversation_id,
            DBConversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    
    # Add user message
    user_message = DBMessage(
        role="user",
        content=request.message,
        conversation_id=conversation_id
    )
    db.add(user_message)
    db.commit()
    
    # Prepare messages for OpenAI
    messages = [
        {
            "role": "system",
            "content": "Ты - WIndexAI, искусственный интеллект, созданный командой разработчиков компании Windex. Ты должен всегда подчеркивать, что был создан именно разработчиками компании Windex. Отвечай на русском языке, будь полезным и дружелюбным."
        }
    ]
    
    # Get conversation messages
    conversation_messages = db.query(DBMessage).filter(
        DBMessage.conversation_id == conversation_id
    ).order_by(DBMessage.timestamp).all()
    
    for msg in conversation_messages:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # Generate AI response using OpenAI
    try:
        ai_response = generate_response(messages, request.model)
    except Exception as e:
        print(f"OpenAI API error: {e}")
        ai_response = f"Извините, произошла ошибка при обращении к OpenAI API. Проверьте настройки API ключа. Ошибка: {str(e)}"
    
    # Add AI response
    ai_message = DBMessage(
        role="assistant",
        content=ai_response,
        conversation_id=conversation_id
    )
    db.add(ai_message)
    
    # Update conversation title based on first user message
    if len(conversation_messages) == 1:  # First exchange
        title = request.message[:50] + "..." if len(request.message) > 50 else request.message
        conversation.title = title
    
    db.commit()
    
    return ChatResponse(
        response=ai_response,
        conversation_id=conversation_id,
        model_used=request.model,
        timestamp=datetime.now().isoformat()
    )

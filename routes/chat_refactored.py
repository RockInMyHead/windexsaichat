"""
Chat routes - Refactored version
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.chat import ChatRequest, ChatResponse, Conversation, Message
from services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])
chat_service = ChatService()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Send a chat message and get AI response"""
    try:
        # Get or create conversation
        conversation = None
        if request.conversation_id:
            conversation = chat_service.get_conversation(
                db, request.conversation_id, current_user.id
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        else:
            # Create new conversation
            conversation = chat_service.create_conversation(
                db,
                current_user.id,
                Conversation(title=f"Chat with {request.model}", model=request.model)
            )

        # Add user message
        user_message = chat_service.add_message(
            db,
            conversation.id,
            Message(content=request.message, role="user")
        )

        # Generate AI response
        ai_response_text = await chat_service.generate_chat_response(
            conversation.id, request.message, request.model
        )

        # Add AI response
        ai_message = chat_service.add_message(
            db,
            conversation.id,
            Message(content=ai_response_text, role="assistant")
        )

        return ChatResponse(
            response=ai_response_text,
            conversation_id=conversation.id,
            message_id=ai_message.id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.get("/conversations", response_model=list[Conversation])
async def get_conversations(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user's conversations"""
    conversations = chat_service.get_user_conversations(db, current_user.id)
    return [Conversation.from_orm(conv) for conv in conversations]


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific conversation with messages"""
    conversation = chat_service.get_conversation(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return Conversation.from_orm(conversation)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a conversation"""
    conversation = chat_service.get_conversation(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    db.delete(conversation)
    db.commit()

    return {"message": "Conversation deleted successfully"}

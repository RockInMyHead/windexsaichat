from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import Conversation as DBConversation
from database import Message as DBMessage
from database import get_db
from routes.auth import User, get_current_user

router = APIRouter()


@router.get("/api/conversations")
async def get_user_conversations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all conversations for current user"""
    conversations = (
        db.query(DBConversation)
        .filter(DBConversation.user_id == current_user.id)
        .order_by(DBConversation.updated_at.desc())
        .all()
    )

    user_conversations = []
    for conv in conversations:
        # Count messages
        message_count = (
            db.query(DBMessage).filter(DBMessage.conversation_id == conv.id).count()
        )
        # Get last message for preview
        last_msg = (
            db.query(DBMessage)
            .filter(DBMessage.conversation_id == conv.id)
            .order_by(DBMessage.timestamp.desc())
            .first()
        )
        snippet = last_msg.content if last_msg else ""
        snippet_date = (
            last_msg.timestamp.isoformat() if last_msg else conv.created_at.isoformat()
        )
        user_conversations.append(
            {
                "id": conv.id,
                "title": conv.title,  # Use conversation title
                "preview": snippet,  # Keep preview for compatibility
                "date": snippet_date,
                "message_count": message_count,
            }
        )

    return {"conversations": user_conversations}


@router.get("/api/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get conversation history"""
    conversation = (
        db.query(DBConversation)
        .filter(
            DBConversation.id == conversation_id,
            DBConversation.user_id == current_user.id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = (
        db.query(DBMessage)
        .filter(DBMessage.conversation_id == conversation_id)
        .order_by(DBMessage.timestamp)
        .all()
    )

    conversation_data = {
        "id": conversation.id,
        "title": conversation.title,
        "timestamp": conversation.created_at.isoformat(),
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in messages
        ],
    }

    return {"conversation": conversation_data}


@router.post("/api/conversations")
async def create_conversation(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Create a new conversation"""
    conversation = DBConversation(title="Новый чат", user_id=current_user.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {"conversation_id": conversation.id}


@router.put("/api/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    title: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update conversation title"""
    conversation = (
        db.query(DBConversation)
        .filter(
            DBConversation.id == conversation_id,
            DBConversation.user_id == current_user.id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.title = title
    db.commit()

    return {"message": "Conversation updated"}


@router.delete("/api/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete conversation"""
    conversation = (
        db.query(DBConversation)
        .filter(
            DBConversation.id == conversation_id,
            DBConversation.user_id == current_user.id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete all messages first
    db.query(DBMessage).filter(DBMessage.conversation_id == conversation_id).delete()

    # Delete conversation
    db.delete(conversation)
    db.commit()

    return {"message": "Conversation deleted"}


@router.delete("/api/conversations")
async def clear_all_conversations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Clear all conversations for current user"""
    conversations = (
        db.query(DBConversation).filter(DBConversation.user_id == current_user.id).all()
    )

    conversation_ids = [conv.id for conv in conversations]

    # Delete all messages
    if conversation_ids:
        db.query(DBMessage).filter(
            DBMessage.conversation_id.in_(conversation_ids)
        ).delete()

    # Delete all conversations
    for conv in conversations:
        db.delete(conv)

    db.commit()

    return {"message": f"Deleted {len(conversations)} conversations"}

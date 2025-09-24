from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime

from routes.auth import get_current_user, User
from routes.chat import conversations

router = APIRouter()

@router.get("/api/conversations")
async def get_user_conversations(current_user: User = Depends(get_current_user)):
    """Get all conversations for current user"""
    user_conversations = []
    for conv_id, conv_data in conversations.items():
        if conv_id.startswith(f"conv_{current_user.username}_"):
            user_conversations.append({
                "id": conv_id,
                "title": conv_data.get("title", "Новый чат"),
                "timestamp": conv_data.get("timestamp", ""),
                "message_count": len(conv_data.get("messages", []))
            })
    
    # Sort by timestamp (newest first)
    user_conversations.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"conversations": user_conversations}

@router.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation": conversations[conversation_id]}

@router.post("/api/conversations")
async def create_conversation(current_user: User = Depends(get_current_user)):
    """Create a new conversation"""
    conversation_id = f"conv_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    conversations[conversation_id] = {
        "id": conversation_id,
        "title": "Новый чат",
        "timestamp": datetime.now().isoformat(),
        "messages": []
    }
    return {"conversation_id": conversation_id}

@router.put("/api/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, title: str, current_user: User = Depends(get_current_user)):
    """Update conversation title"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if user owns this conversation
    if not conversation_id.startswith(f"conv_{current_user.username}_"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    conversations[conversation_id]["title"] = title
    return {"message": "Conversation updated"}

@router.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete conversation"""
    if conversation_id in conversations:
        del conversations[conversation_id]
        return {"message": "Conversation deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")

@router.delete("/api/conversations")
async def clear_all_conversations(current_user: User = Depends(get_current_user)):
    """Clear all conversations for current user"""
    user_conversations = [conv_id for conv_id in conversations.keys() 
                         if conv_id.startswith(f"conv_{current_user.username}_")]
    
    for conv_id in user_conversations:
        del conversations[conv_id]
    
    return {"message": f"Deleted {len(user_conversations)} conversations"}

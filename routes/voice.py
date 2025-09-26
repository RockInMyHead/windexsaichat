from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
import os
import uuid
import tempfile
import shutil

from routes.auth import get_current_user, User
from utils.openai_client import generate_response, transcribe_audio, text_to_speech
from database import get_db, Conversation as DBConversation, Message as DBMessage

router = APIRouter()

# Pydantic models
class VoiceMessageRequest(BaseModel):
    conversation_id: Optional[int] = None
    model: str

class VoiceMessageResponse(BaseModel):
    response: str
    conversation_id: int
    model_used: str
    timestamp: str
    audio_url: Optional[str] = None

@router.post("/api/voice/upload", response_model=VoiceMessageResponse)
async def upload_voice_message(
    audio_file: UploadFile = File(...),
    conversation_id: Optional[int] = Form(None),
    model: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process voice message"""
    
    # Validate audio file
    if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an audio file"
        )
    
    # Create uploads directory if it doesn't exist
    uploads_dir = "uploads/audio"
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = audio_file.filename.split('.')[-1] if '.' in audio_file.filename else 'webm'
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(uploads_dir, unique_filename)
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        # Transcribe audio using OpenAI Whisper
        transcribed_text = transcribe_audio(file_path)
        
        if not transcribed_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not transcribe audio"
            )
        
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation = DBConversation(
                title="Новый чат",
                user_id=current_user.id
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            conversation_id = conversation.id
        else:
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
        
        # Add user voice message
        user_message = DBMessage(
            role="user",
            content=transcribed_text,
            message_type="voice",
            audio_url=f"/uploads/audio/{unique_filename}",
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
        
        # Generate AI response
        try:
            ai_response = generate_response(messages, model)
        except Exception as e:
            print(f"OpenAI API error: {e}")
            ai_response = f"Извините, произошла ошибка при обращении к OpenAI API. Проверьте настройки API ключа. Ошибка: {str(e)}"
        
        # Generate audio response using text-to-speech
        audio_response_url = None
        try:
            audio_response_path = text_to_speech(ai_response)
            if audio_response_path:
                # Move to uploads directory
                response_filename = f"{uuid.uuid4()}.mp3"
                response_file_path = os.path.join(uploads_dir, response_filename)
                shutil.move(audio_response_path, response_file_path)
                audio_response_url = f"/uploads/audio/{response_filename}"
        except Exception as e:
            print(f"Text-to-speech error: {e}")
            # Continue without audio response
        
        # Add AI response
        ai_message = DBMessage(
            role="assistant",
            content=ai_response,
            message_type="voice" if audio_response_url else "text",
            audio_url=audio_response_url,
            conversation_id=conversation_id
        )
        db.add(ai_message)
        
        # Update conversation title based on first user message
        if len(conversation_messages) == 1:  # First exchange
            title = transcribed_text[:50] + "..." if len(transcribed_text) > 50 else transcribed_text
            conversation.title = title
        
        db.commit()
        
        return VoiceMessageResponse(
            response=ai_response,
            conversation_id=conversation_id,
            model_used=model,
            timestamp=datetime.now().isoformat(),
            audio_url=audio_response_url
        )
        
    except Exception as e:
        # Clean up file if error occurred
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice message: {str(e)}"
        )

@router.get("/uploads/audio/{filename}")
async def get_audio_file(filename: str):
    """Serve audio files"""
    file_path = os.path.join("uploads/audio", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )


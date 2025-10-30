import mimetypes
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import (APIRouter, Depends, File, Form, HTTPException, UploadFile,
                     status)
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Conversation as DBConversation
from database import Document as DBDocument
from database import Message as DBMessage
from database import get_db
from routes.auth import User, get_current_user
from utils.document_parser import parse_document
from utils.openai_client import generate_response

router = APIRouter()


# Pydantic models
class DocumentUploadRequest(BaseModel):
    conversation_id: Optional[int] = None
    model: str


class DocumentUploadResponse(BaseModel):
    response: str
    conversation_id: int
    model_used: str
    timestamp: str
    document_id: int
    document_name: str


class DocumentInfo(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    upload_date: datetime
    content_preview: str


# Supported file types
SUPPORTED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
    "text/plain": "txt",
    "text/csv": "csv",
    "application/rtf": "rtf",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/bmp": "bmp",
    "image/tiff": "tiff",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: Optional[int] = Form(None),
    model: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload and process document"""

    # Validate file type
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported types: {', '.join(SUPPORTED_TYPES.keys())}",
        )

    # Validate file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    # Create uploads directory if it doesn't exist
    uploads_dir = "uploads/documents"
    os.makedirs(uploads_dir, exist_ok=True)

    # Generate unique filename
    file_extension = SUPPORTED_TYPES[file.content_type]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(uploads_dir, unique_filename)

    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        # Parse document content
        extracted_content = parse_document(file_path, file.content_type)
        
        print(f"Document parsing result: {len(extracted_content) if extracted_content else 0} characters extracted")
        if extracted_content:
            print(f"First 200 chars: {extracted_content[:200]}")

        if not extracted_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract content from document",
            )

        # Create document record
        document = DBDocument(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(file_content),
            file_type=file_extension,
            content=extracted_content,
            user_id=current_user.id,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Generate conversation ID if not provided
        if not conversation_id:
            conversation = DBConversation(
                title=f"Документ: {file.filename}", user_id=current_user.id
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            conversation_id = conversation.id
        else:
            # Verify conversation belongs to user
            conversation = (
                db.query(DBConversation)
                .filter(
                    DBConversation.id == conversation_id,
                    DBConversation.user_id == current_user.id,
                )
                .first()
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found",
                )

        # Add user document message
        user_message = DBMessage(
            role="user",
            content=f"Загружен документ: {file.filename}",
            message_type="document",
            document_id=document.id,
            conversation_id=conversation_id,
        )
        db.add(user_message)
        db.commit()

        # Prepare messages for OpenAI with document content
        messages = [
            {
                "role": "system",
                "content": f"""Ты - WIndexAI, искусственный интеллект, созданный командой разработчиков компании Windex.

Пользователь загрузил документ "{file.filename}" и хочет, чтобы ты его проанализировал.

ТВОЯ ЗАДАЧА:
• Проанализируй загруженный документ
• Если пользователь не задал конкретный вопрос, дай краткое резюме документа
• Если задал вопрос - ответь на него, используя информацию из документа
• Отвечай на русском языке, будь полезным и дружелюбным

СОДЕРЖИМОЕ ЗАГРУЖЕННОГО ДОКУМЕНТА:
{extracted_content[:4000] if extracted_content else "Содержимое документа не удалось извлечь"}

ВАЖНО: Документ был успешно загружен и обработан. Используй информацию выше для ответа пользователю.""",
            }
        ]

        # Get conversation messages
        conversation_messages = (
            db.query(DBMessage)
            .filter(DBMessage.conversation_id == conversation_id)
            .order_by(DBMessage.timestamp)
            .all()
        )

        for msg in conversation_messages:
            messages.append({"role": msg.role, "content": msg.content})

        # Generate AI response
        try:
            print(f"Sending {len(messages)} messages to OpenAI API")
            print(f"System message length: {len(messages[0]['content'])} characters")
            ai_response = await generate_response(messages, model)
        except Exception as e:
            print(f"OpenAI API error: {e}")
            ai_response = f"Извините, произошла ошибка при обращении к OpenAI API. Проверьте настройки API ключа. Ошибка: {str(e)}"

        # Add AI response
        ai_message = DBMessage(
            role="assistant", content=ai_response, conversation_id=conversation_id
        )
        db.add(ai_message)

        # Update conversation title based on document
        if len(conversation_messages) == 1:  # First exchange
            title = f"Документ: {file.filename}"
            conversation.title = title

        db.commit()

        return DocumentUploadResponse(
            response=ai_response,
            conversation_id=conversation_id,
            model_used=model,
            timestamp=datetime.now().isoformat(),
            document_id=document.id,
            document_name=file.filename,
        )

    except Exception as e:
        # Clean up file if error occurred
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}",
        )


@router.get("/api/documents", response_model=List[DocumentInfo])
async def get_user_documents(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all documents for current user"""

    documents = (
        db.query(DBDocument)
        .filter(DBDocument.user_id == current_user.id)
        .order_by(DBDocument.upload_date.desc())
        .all()
    )

    return [
        DocumentInfo(
            id=doc.id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            file_size=doc.file_size,
            file_type=doc.file_type,
            upload_date=doc.upload_date,
            content_preview=(
                doc.content[:200] + "..."
                if doc.content and len(doc.content) > 200
                else doc.content or ""
            ),
        )
        for doc in documents
    ]


@router.get("/api/documents/{document_id}")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get specific document by ID"""

    document = (
        db.query(DBDocument)
        .filter(DBDocument.id == document_id, DBDocument.user_id == current_user.id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return DocumentInfo(
        id=document.id,
        filename=document.filename,
        original_filename=document.original_filename,
        file_size=document.file_size,
        file_type=document.file_type,
        upload_date=document.upload_date,
        content_preview=(
            document.content[:500] + "..."
            if document.content and len(document.content) > 500
            else document.content or ""
        ),
    )


@router.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete document"""

    document = (
        db.query(DBDocument)
        .filter(DBDocument.id == document_id, DBDocument.user_id == current_user.id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Delete file from filesystem
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    # Delete from database
    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully"}


@router.get("/uploads/documents/{filename}")
async def get_document_file(filename: str):
    """Serve document files"""
    file_path = os.path.join("uploads/documents", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found"
        )

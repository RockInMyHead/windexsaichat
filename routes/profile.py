from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database import User as DBUser, Conversation, Message, Document, Deployment
from database import get_db
from routes.auth import get_current_user, User

router = APIRouter(prefix="/api/profile", tags=["profile"])


# Pydantic models
class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    subscription_plan: str
    subscription_expires_at: Optional[datetime] = None
    total_conversations: int = 0
    total_messages: int = 0
    total_documents: int = 0
    total_deployments: int = 0
    last_activity: Optional[datetime] = None


class UserStats(BaseModel):
    total_conversations: int
    total_messages: int
    total_documents: int
    total_deployments: int
    messages_this_month: int
    conversations_this_month: int
    most_active_day: Optional[str] = None
    average_messages_per_conversation: float = 0.0


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.get("/me", response_model=UserProfile)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить профиль текущего пользователя"""
    db_user = db.query(DBUser).filter(DBUser.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Подсчитываем статистику
    total_conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).count()
    total_messages = db.query(Message).join(Conversation).filter(Conversation.user_id == current_user.id).count()
    total_documents = db.query(Document).filter(Document.user_id == current_user.id).count()
    total_deployments = db.query(Deployment).filter(Deployment.user_id == current_user.id).count()
    
    # Последняя активность
    last_message = db.query(Message).join(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(desc(Message.timestamp)).first()
    
    last_activity = last_message.timestamp if last_message else None
    
    return UserProfile(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        created_at=db_user.created_at,
        subscription_plan=db_user.subscription_plan,
        subscription_expires_at=db_user.subscription_expires_at,
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_documents=total_documents,
        total_deployments=total_deployments,
        last_activity=last_activity
    )


@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить детальную статистику пользователя"""
    # Общая статистика
    total_conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).count()
    total_messages = db.query(Message).join(Conversation).filter(Conversation.user_id == current_user.id).count()
    total_documents = db.query(Document).filter(Document.user_id == current_user.id).count()
    total_deployments = db.query(Deployment).filter(Deployment.user_id == current_user.id).count()
    
    # Статистика за текущий месяц
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    messages_this_month = db.query(Message).join(Conversation).filter(
        Conversation.user_id == current_user.id,
        Message.timestamp >= current_month
    ).count()
    
    conversations_this_month = db.query(Conversation).filter(
        Conversation.user_id == current_user.id,
        Conversation.created_at >= current_month
    ).count()
    
    # Самый активный день (по количеству сообщений)
    most_active_day_query = db.query(
        func.date(Message.timestamp).label('date'),
        func.count(Message.id).label('count')
    ).join(Conversation).filter(
        Conversation.user_id == current_user.id
    ).group_by(func.date(Message.timestamp)).order_by(desc('count')).first()
    
    most_active_day = most_active_day_query.date if most_active_day_query else None
    
    # Среднее количество сообщений на разговор
    avg_messages = total_messages / total_conversations if total_conversations > 0 else 0.0
    
    return UserStats(
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_documents=total_documents,
        total_deployments=total_deployments,
        messages_this_month=messages_this_month,
        conversations_this_month=conversations_this_month,
        most_active_day=most_active_day,
        average_messages_per_conversation=round(avg_messages, 2)
    )


@router.get("/recent-activity")
async def get_recent_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Получить последнюю активность пользователя"""
    # Последние разговоры
    recent_conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(desc(Conversation.updated_at)).limit(limit).all()
    
    # Последние документы
    recent_documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(desc(Document.upload_date)).limit(5).all()
    
    # Последние деплои
    recent_deployments = db.query(Deployment).filter(
        Deployment.user_id == current_user.id
    ).order_by(desc(Deployment.created_at)).limit(5).all()
    
    return {
        "recent_conversations": [
            {
                "id": conv.id,
                "title": conv.title,
                "updated_at": conv.updated_at,
                "message_count": db.query(Message).filter(Message.conversation_id == conv.id).count()
            }
            for conv in recent_conversations
        ],
        "recent_documents": [
            {
                "id": doc.id,
                "filename": doc.original_filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "upload_date": doc.upload_date
            }
            for doc in recent_documents
        ],
        "recent_deployments": [
            {
                "id": dep.id,
                "name": dep.name,
                "status": dep.status,
                "created_at": dep.created_at
            }
            for dep in recent_deployments
        ]
    }


@router.put("/update", response_model=UserProfile)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить профиль пользователя"""
    db_user = db.query(DBUser).filter(DBUser.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверяем уникальность username
    if user_update.username and user_update.username != db_user.username:
        existing_user = db.query(DBUser).filter(DBUser.username == user_update.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        db_user.username = user_update.username
    
    # Проверяем уникальность email
    if user_update.email and user_update.email != db_user.email:
        existing_user = db.query(DBUser).filter(DBUser.email == user_update.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already taken")
        db_user.email = user_update.email
    
    db.commit()
    db.refresh(db_user)
    
    # Возвращаем обновленный профиль
    return await get_profile(current_user, db)


@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Изменить пароль пользователя"""
    from utils.auth_utils import verify_password, get_password_hash
    
    db_user = db.query(DBUser).filter(DBUser.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверяем текущий пароль
    if not verify_password(password_change.current_password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Обновляем пароль
    db_user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}


@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить аккаунт пользователя"""
    db_user = db.query(DBUser).filter(DBUser.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Удаляем все связанные данные
    # Сначала удаляем сообщения
    db.query(Message).join(Conversation).filter(Conversation.user_id == current_user.id).delete()
    
    # Затем разговоры
    db.query(Conversation).filter(Conversation.user_id == current_user.id).delete()
    
    # Документы
    db.query(Document).filter(Document.user_id == current_user.id).delete()
    
    # Деплои
    db.query(Deployment).filter(Deployment.user_id == current_user.id).delete()
    
    # И наконец пользователя
    db.delete(db_user)
    db.commit()
    
    return {"message": "Account deleted successfully"}


@router.get("/subscription")
async def get_subscription_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить информацию о подписке"""
    db_user = db.query(DBUser).filter(DBUser.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_active = True
    if db_user.subscription_expires_at:
        is_active = db_user.subscription_expires_at > datetime.utcnow()
    
    return {
        "plan": db_user.subscription_plan,
        "expires_at": db_user.subscription_expires_at,
        "is_active": is_active,
        "features": {
            "free": {
                "max_conversations": 10,
                "max_documents": 5,
                "max_deployments": 2,
                "ai_models": ["gpt-4o-mini"]
            },
            "pro": {
                "max_conversations": -1,  # unlimited
                "max_documents": -1,  # unlimited
                "max_deployments": -1,  # unlimited
                "ai_models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
            }
        }
    }


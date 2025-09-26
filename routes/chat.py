from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import re

from routes.auth import get_current_user, User
from utils.openai_client import generate_response, format_messages_for_openai
from utils.web_search import search_web, format_search_results
from database import get_db, Conversation as DBConversation, Message as DBMessage

router = APIRouter()

def should_search_web(message: str) -> bool:
    """Определяет, нужен ли веб-поиск для сообщения"""
    search_keywords = [
        'найди', 'поиск', 'актуальн', 'новости', 'сейчас', 'сегодня', 
        'последние', 'тренд', 'курс', 'погода', 'цены', 'события',
        'что происходит', 'как дела', 'статистика', 'данные',
        'информация о', 'расскажи про', 'что нового', 'какая погода'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in search_keywords)

def extract_search_query(message: str) -> str:
    """Извлекает поисковый запрос из сообщения"""
    # Спец. обработка для погоды: формируем более точный запрос
    message_lower = message.lower()
    if 'погод' in message_lower:
        city = extract_weather_city(message)
        if city:
            # Формируем целевой запрос под погоду
            return f"погода {city} сейчас температура прогноз"
        # Если город не извлекли, оставляем слово погода и просим текущие данные
        return "погода сейчас температура прогноз"

    # Убираем общие фразы, оставляем суть запроса
    patterns_to_remove = [
        r'найди\s*',
        r'поиск\s*',
        r'расскажи\s*про\s*',
        r'что\s*такое\s*',
        r'информация\s*о\s*',
        r'какая\s*погода\s*',
        r'сейчас\s*',
        r'сегодня\s*',
        r'последние\s*новости\s*о\s*',
        r'что\s*происходит\s*с\s*',
        r'как\s*дела\s*с\s*',
        r'статистика\s*по\s*',
        r'данные\s*о\s*'
    ]
    
    query = message
    for pattern in patterns_to_remove:
        query = re.sub(pattern, '', query, flags=re.IGNORECASE)
    
    return query.strip()

def extract_weather_city(message: str) -> str:
    """Пытается извлечь город из запроса о погоде"""
    # Паттерны вида: "погода в Москве", "какая погода в санкт-петербурге", "погода во Владивостоке"
    match = re.search(r'погод[аы]\s*(?:в|во)\s+([A-Za-zА-Яа-яёЁ\-\s]+)', message, flags=re.IGNORECASE)
    if match:
        # Обрезаем по знакам препинания, если есть хвост
        city = match.group(1)
        city = re.split(r'[\?\!\.,;:\n\r\t]', city)[0]
        city = city.strip()
        # Нормализуем регистр
        if city:
            return city
    return ""

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
    
    # Проверяем, нужен ли веб-поиск
    web_search_results = ""
    if should_search_web(request.message):
        
        # Извлекаем поисковый запрос
        search_query = extract_search_query(request.message)
        if not search_query:
            search_query = request.message
        
        # Выполняем поиск
        try:
            search_results = search_web(search_query, num_results=3)
            web_search_results = format_search_results(search_results)
        except Exception as e:
            web_search_results = "Ошибка при поиске в интернете."
    
    # Prepare messages for OpenAI
    if web_search_results:
        # Для запросов с веб-поиском
        system_content = f"""Ты - WIndexAI, искусственный интеллект, созданный командой разработчиков компании Windex. Ты должен всегда подчеркивать, что был создан именно разработчиками компании Windex.

Твоя задача - дать полный и точный ответ на основе найденной информации.

ВАЖНО:
• Используй информацию из результатов поиска для ответа
• Если информация противоречивая, укажи это
• Ссылайся на источники когда это уместно
• Если информации недостаточно, скажи об этом честно
• Отвечай на русском языке, будь полезным и дружелюбным

РЕЗУЛЬТАТЫ ПОИСКА:
{web_search_results}

Теперь ответь на вопрос пользователя, используя эту информацию."""
    else:
        # Для обычных запросов
        system_content = "Ты - WIndexAI, искусственный интеллект, созданный командой разработчиков компании Windex. Ты должен всегда подчеркивать, что был создан именно разработчиками компании Windex. Отвечай на русском языке, будь полезным и дружелюбным."
    
    messages = [
        {
            "role": "system",
            "content": system_content
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

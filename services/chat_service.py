"""
Chat service with business logic
"""
import re
from typing import List, Optional

from sqlalchemy.orm import Session

from schemas.chat import Conversation, ConversationCreate, Message, MessageCreate
from utils.openai_client import generate_response, format_messages_for_openai

# Import database models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import Conversation as DBConversation, Message as DBMessage


class ChatService:
    def __init__(self):
        self.no_search_patterns = [
            # Приветствия и благодарности
            r'^(привет|здравствуй|добрый день|доброе утро|добрый вечер|спасибо|благодар|пока|до свидания)$',
            r'^(hi|hello|hey|thanks|thank you|bye|goodbye)$',
            # Простые ответы на вопросы бота
            r'как дела|что делаешь|кто ты|что ты умеешь',
            r'расскажи о себе|что ты можешь',
            # Команды управления
            r'очистить|удалить|новый чат|стоп|хватит',
            r'clear|delete|new chat|stop',
            # Математические операции (простые)
            r'^\d+[\+\-\*\/]\d+.*$',
            r'^вычисли|посчитай|сколько будет',
            # Очень короткие сообщения (1-2 слова)
            r'^\w{1,10}(\s+\w{1,10})?$',
        ]

    def should_search_web(self, message: str) -> bool:
        """Определяет, нужен ли веб-поиск для сообщения"""
        message_lower = message.lower().strip()

        # Проверяем, попадает ли сообщение под исключения
        for pattern in self.no_search_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return False

        return True

    def create_conversation(self, db: Session, user_id: int, conversation: ConversationCreate) -> DBConversation:
        """Create a new conversation"""
        db_conversation = DBConversation(
            user_id=user_id,
            title=conversation.title,
            model=conversation.model
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation

    def get_conversation(self, db: Session, conversation_id: int, user_id: int) -> Optional[DBConversation]:
        """Get a conversation by ID for a specific user"""
        return db.query(DBConversation).filter(
            DBConversation.id == conversation_id,
            DBConversation.user_id == user_id
        ).first()

    def get_user_conversations(self, db: Session, user_id: int, limit: int = 50) -> List[DBConversation]:
        """Get all conversations for a user"""
        return db.query(DBConversation).filter(
            DBConversation.user_id == user_id
        ).order_by(DBConversation.updated_at.desc()).limit(limit).all()

    def add_message(self, db: Session, conversation_id: int, message: MessageCreate) -> DBMessage:
        """Add a message to a conversation"""
        db_message = DBMessage(
            conversation_id=conversation_id,
            content=message.content,
            role=message.role
        )
        db.add(db_message)

        # Update conversation timestamp
        db.query(DBConversation).filter(
            DBConversation.id == conversation_id
        ).update({"updated_at": db_message.created_at})

        db.commit()
        db.refresh(db_message)
        return db_message

    def get_conversation_messages(self, db: Session, conversation_id: int, limit: int = 100) -> List[DBMessage]:
        """Get all messages for a conversation"""
        return db.query(DBMessage).filter(
            DBMessage.conversation_id == conversation_id
        ).order_by(DBMessage.created_at).limit(limit).all()

    async def generate_chat_response(self, conversation_id: int, user_message: str, model: str) -> str:
        """Generate AI response for chat"""
        # For now, use the existing logic
        # This should be moved to a more sophisticated implementation
        return await generate_response(user_message, model)

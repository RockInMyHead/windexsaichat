"""
Unit tests for ChatService
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from services.chat_service import ChatService
from schemas.chat import ConversationCreate, Message


class TestChatService:
    def setup_method(self):
        """Setup for each test method"""
        self.chat_service = ChatService()

    def create_test_user(self, db_session, username_suffix=""):
        """Helper method to create a unique test user"""
        from database import User as DBUser
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        test_user = DBUser(
            username=f"testuser_{unique_id}{username_suffix}",
            email=f"test_{unique_id}{username_suffix}@example.com",
            hashed_password="hash"
        )
        db_session.add(test_user)
        db_session.commit()
        return test_user

    def test_should_search_web_greeting(self):
        """Test web search decision for greetings"""
        assert not self.chat_service.should_search_web("привет")
        assert not self.chat_service.should_search_web("hello")
        assert not self.chat_service.should_search_web("спасибо")

    def test_should_search_web_questions(self):
        """Test web search decision for questions"""
        assert self.chat_service.should_search_web("что такое python")
        assert self.chat_service.should_search_web("как работает ИИ")
        assert self.chat_service.should_search_web("что такое quantum computing")

    def test_should_search_web_commands(self):
        """Test web search decision for commands"""
        assert not self.chat_service.should_search_web("очистить чат")
        assert not self.chat_service.should_search_web("новый разговор")
        assert not self.chat_service.should_search_web("стоп")

    def test_should_search_web_math(self):
        """Test web search decision for math operations"""
        assert not self.chat_service.should_search_web("2 + 2")
        assert not self.chat_service.should_search_web("вычисли 5*3")
        assert self.chat_service.should_search_web("реши уравнение x^2")

    def test_should_search_web_short_messages(self):
        """Test web search decision for very short messages"""
        assert not self.chat_service.should_search_web("ok")
        assert not self.chat_service.should_search_web("да")
        assert self.chat_service.should_search_web("что такое quantum computing")

    def test_create_conversation(self, db_session):
        """Test conversation creation"""
        # Create test user
        test_user = self.create_test_user(db_session)

        conv_data = ConversationCreate(title="Test Chat", model="gpt-4o-mini")
        conversation = self.chat_service.create_conversation(db_session, test_user.id, conv_data)

        assert conversation.user_id == test_user.id
        assert conversation.title == "Test Chat"
        assert conversation.model_used == "gpt-4o-mini"

    def test_get_conversation_found(self, db_session):
        """Test getting existing conversation"""
        # Create test user
        test_user = self.create_test_user(db_session)

        # Create conversation
        conv_data = ConversationCreate(title="Test Chat", model="gpt-4o-mini")
        created_conv = self.chat_service.create_conversation(db_session, test_user.id, conv_data)

        # Get conversation
        found_conv = self.chat_service.get_conversation(db_session, created_conv.id, test_user.id)
        assert found_conv is not None
        assert found_conv.id == created_conv.id

    def test_get_conversation_not_found(self, db_session):
        """Test getting non-existent conversation"""
        # Create test user
        test_user = self.create_test_user(db_session)

        found_conv = self.chat_service.get_conversation(db_session, 999, test_user.id)
        assert found_conv is None

    def test_get_conversation_wrong_user(self, db_session):
        """Test getting conversation of another user"""
        # Create two users
        user1 = self.create_test_user(db_session, "_user1")
        user2 = self.create_test_user(db_session, "_user2")

        # Create conversation for user1
        conv_data = ConversationCreate(title="Test Chat", model="gpt-4o-mini")
        created_conv = self.chat_service.create_conversation(db_session, user1.id, conv_data)

        # Try to get it as user2
        found_conv = self.chat_service.get_conversation(db_session, created_conv.id, user2.id)
        assert found_conv is None

    def test_get_user_conversations(self, db_session):
        """Test getting user's conversations"""
        # Create test user
        test_user = self.create_test_user(db_session)

        # Create multiple conversations
        for i in range(3):
            conv_data = ConversationCreate(title=f"Chat {i}", model="gpt-4o-mini")
            self.chat_service.create_conversation(db_session, test_user.id, conv_data)

        conversations = self.chat_service.get_user_conversations(db_session, test_user.id)
        assert len(conversations) == 3

        # Check ordering (should be by updated_at desc)
        assert conversations[0].title == "Chat 2"
        assert conversations[1].title == "Chat 1"
        assert conversations[2].title == "Chat 0"

    def test_get_user_conversations_limit(self, db_session):
        """Test getting user's conversations with limit"""
        # Create test user
        test_user = self.create_test_user(db_session)

        # Create 5 conversations
        for i in range(5):
            conv_data = ConversationCreate(title=f"Chat {i}", model="gpt-4o-mini")
            self.chat_service.create_conversation(db_session, test_user.id, conv_data)

        conversations = self.chat_service.get_user_conversations(db_session, test_user.id, limit=3)
        assert len(conversations) == 3

    def test_add_message(self, db_session):
        """Test adding message to conversation"""
        # Create test user
        test_user = self.create_test_user(db_session)

        # Create conversation
        conv_data = ConversationCreate(title="Test Chat", model="gpt-4o-mini")
        conversation = self.chat_service.create_conversation(db_session, test_user.id, conv_data)

        # Add message
        message_data = Message(content="Hello, AI!", role="user")
        message = self.chat_service.add_message(db_session, conversation.id, message_data)

        assert message.conversation_id == conversation.id
        assert message.content == "Hello, AI!"
        assert message.role == "user"

    def test_get_conversation_messages(self, db_session):
        """Test getting conversation messages"""
        # Create test user
        test_user = self.create_test_user(db_session)

        # Create conversation
        conv_data = ConversationCreate(title="Test Chat", model="gpt-4o-mini")
        conversation = self.chat_service.create_conversation(db_session, test_user.id, conv_data)

        # Add multiple messages
        messages_data = [
            Message(content="Hello", role="user"),
            Message(content="Hi there!", role="assistant"),
            Message(content="How are you?", role="user"),
        ]

        for msg_data in messages_data:
            self.chat_service.add_message(db_session, conversation.id, msg_data)

        # Get messages
        messages = self.chat_service.get_conversation_messages(db_session, conversation.id)
        assert len(messages) == 3
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi there!"
        assert messages[2].content == "How are you?"

    @patch('services.chat_service.generate_response', new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_generate_chat_response(self, mock_generate):
        """Test chat response generation"""
        mock_generate.return_value = "AI response"

        response = await self.chat_service.generate_chat_response(1, "user message", "gpt-4o-mini")

        assert response == "AI response"
        mock_generate.assert_called_once_with("user message", "gpt-4o-mini")

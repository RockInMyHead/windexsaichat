"""
Integration tests for chat API
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestChatAPI:
    def get_auth_token(self, client: TestClient) -> str:
        """Helper method to get authentication token"""
        # Register user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        client.post("/api/auth/register", json=user_data)

        # Login
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        response = client.post("/api/auth/login", data=login_data)
        return response.json()["access_token"]

    def test_get_models(self, client: TestClient):
        """Test getting available models"""
        response = client.get("/api/models")
        assert response.status_code == 200

        data = response.json()
        assert "models" in data
        assert "gpt-4o-mini" in data["models"]
        assert "gpt-4o" in data["models"]

        # Check model structure
        model = data["models"]["gpt-4o-mini"]
        assert "id" in model
        assert "name" in model
        assert "description" in model
        assert "max_tokens" in model
        assert "capabilities" in model

    @patch('services.chat_service.ChatService.generate_chat_response', new_callable=AsyncMock)
    def test_chat_success(self, mock_generate, client: TestClient):
        """Test successful chat interaction"""
        mock_generate.return_value = "AI response to user message"

        token = self.get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        chat_data = {
            "message": "Hello, AI!",
            "model": "gpt-4o-mini"
        }

        response = client.post("/api/chat/", json=chat_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
        assert "message_id" in data
        assert data["response"] == "AI response to user message"

    def test_chat_unauthenticated(self, client: TestClient):
        """Test chat without authentication"""
        chat_data = {
            "message": "Hello, AI!",
            "model": "gpt-4o-mini"
        }

        response = client.post("/api/chat/", json=chat_data)
        assert response.status_code == 401

    @patch('services.chat_service.ChatService.generate_chat_response', new_callable=AsyncMock)
    def test_chat_with_conversation(self, mock_generate, client: TestClient):
        """Test chat with existing conversation"""
        mock_generate.return_value = "Follow-up response"

        token = self.get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # First message
        chat_data1 = {
            "message": "Hello, AI!",
            "model": "gpt-4o-mini"
        }
        response1 = client.post("/api/chat/", json=chat_data1, headers=headers)
        assert response1.status_code == 200
        conversation_id = response1.json()["conversation_id"]

        # Second message in same conversation
        chat_data2 = {
            "message": "How are you?",
            "model": "gpt-4o-mini",
            "conversation_id": conversation_id
        }
        response2 = client.post("/api/chat/", json=chat_data2, headers=headers)

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["conversation_id"] == conversation_id
        assert data2["response"] == "Follow-up response"

    def test_get_conversations(self, client: TestClient):
        """Test getting user conversations"""
        token = self.get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Create some conversations by sending messages
        for i in range(3):
            chat_data = {
                "message": f"Message {i}",
                "model": "gpt-4o-mini"
            }
            with patch('services.chat_service.ChatService.generate_chat_response', new_callable=AsyncMock) as mock:
                mock.return_value = f"Response {i}"
                client.post("/api/chat/", json=chat_data, headers=headers)

        # Get conversations
        response = client.get("/api/chat/conversations", headers=headers)
        assert response.status_code == 200

        conversations = response.json()
        assert isinstance(conversations, list)
        assert len(conversations) == 3

        # Check conversation structure
        conv = conversations[0]
        assert "id" in conv
        assert "title" in conv
        assert "model" in conv
        assert "created_at" in conv
        assert "updated_at" in conv

    def test_get_conversation_by_id(self, client: TestClient):
        """Test getting specific conversation"""
        token = self.get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Create conversation
        chat_data = {
            "message": "Test message",
            "model": "gpt-4o-mini"
        }
        with patch('services.chat_service.ChatService.generate_chat_response', new_callable=AsyncMock) as mock:
            mock.return_value = "Test response"
            response = client.post("/api/chat/", json=chat_data, headers=headers)

        conversation_id = response.json()["conversation_id"]

        # Get conversation by ID
        response = client.get(f"/api/chat/conversations/{conversation_id}", headers=headers)
        assert response.status_code == 200

        conversation = response.json()
        assert conversation["id"] == conversation_id
        assert "messages" in conversation
        assert len(conversation["messages"]) == 2  # user + assistant

    def test_get_conversation_not_found(self, client: TestClient):
        """Test getting non-existent conversation"""
        token = self.get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/chat/conversations/999", headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_conversation_wrong_user(self, client: TestClient):
        """Test getting conversation of another user"""
        # Create first user and conversation
        token1 = self.get_auth_token(client)
        headers1 = {"Authorization": f"Bearer {token1}"}

        chat_data = {"message": "Test message", "model": "gpt-4o-mini"}
        with patch('services.chat_service.ChatService.generate_chat_response', new_callable=AsyncMock) as mock:
            mock.return_value = "Test response"
            response = client.post("/api/chat/", json=chat_data, headers=headers1)

        conversation_id = response.json()["conversation_id"]

        # Create second user
        user_data2 = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123"
        }
        client.post("/api/auth/register", json=user_data2)

        login_data2 = {"username": "user2", "password": "password123"}
        token2_response = client.post("/api/auth/login", data=login_data2)
        token2 = token2_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Try to access conversation of first user
        response = client.get(f"/api/chat/conversations/{conversation_id}", headers=headers2)
        assert response.status_code == 404

    def test_delete_conversation(self, client: TestClient):
        """Test deleting conversation"""
        token = self.get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Create conversation
        chat_data = {"message": "Test message", "model": "gpt-4o-mini"}
        with patch('services.chat_service.ChatService.generate_chat_response', new_callable=AsyncMock) as mock:
            mock.return_value = "Test response"
            response = client.post("/api/chat/", json=chat_data, headers=headers)

        conversation_id = response.json()["conversation_id"]

        # Delete conversation
        response = client.delete(f"/api/chat/conversations/{conversation_id}", headers=headers)
        assert response.status_code == 200
        assert "deleted" in response.json()["message"]

        # Try to get deleted conversation
        response = client.get(f"/api/chat/conversations/{conversation_id}", headers=headers)
        assert response.status_code == 404

"""
Integration tests for API endpoints
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException


class TestAIEditorEndpoints:
    """Integration tests for AI Editor endpoints"""

    def test_get_llm_thoughts_empty(self, client):
        """Test getting LLM thoughts when none exist"""
        # Mock authentication
        with patch('routes.ai_editor.router.get_current_user') as mock_user:
            mock_user.return_value.id = 1

            response = client.get("/api/ai-editor/thoughts/test_conversation")

            assert response.status_code == 200
            data = response.json()
            assert "thoughts" in data
            assert data["thoughts"] == []

    def test_get_conversations_unauthorized(self, client):
        """Test getting conversations without authentication"""
        response = client.get("/api/ai-editor/conversations")

        assert response.status_code == 401

    @patch('routes.ai_editor.router.get_current_user')
    @patch('routes.ai_editor.router.get_db')
    def test_get_conversations_empty(self, mock_db, mock_user, client):
        """Test getting conversations when user has none"""
        # Mock user
        mock_user.return_value.id = 1

        # Mock empty database query
        mock_session = mock_db.return_value
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = []

        response = client.get("/api/ai-editor/conversations")

        assert response.status_code == 200
        data = response.json()
        assert data["conversations"] == []

    @patch('routes.ai_editor.router.get_current_user')
    @patch('routes.ai_editor.router.get_db')
    def test_get_conversation_not_found(self, mock_db, mock_user, client):
        """Test getting non-existent conversation"""
        # Mock user
        mock_user.return_value.id = 1

        # Mock database query returning None
        mock_session = mock_db.return_value
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = None

        response = client.get("/api/ai-editor/conversations/999")

        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]

    @patch('routes.ai_editor.router.get_current_user')
    @patch('routes.ai_editor.router.get_db')
    def test_delete_conversation_not_found(self, mock_db, mock_user, client):
        """Test deleting non-existent conversation"""
        # Mock user
        mock_user.return_value.id = 1

        # Mock database query returning None
        mock_session = mock_db.return_value
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = None

        response = client.delete("/api/ai-editor/conversations/999")

        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]

    @patch('routes.ai_editor.router.get_current_user')
    @patch('routes.ai_editor.router.get_db')
    def test_delete_conversation_success(self, mock_db, mock_user, client):
        """Test successful conversation deletion"""
        # Mock user
        mock_user.return_value.id = 1

        # Mock conversation object
        mock_conversation = AsyncMock()
        mock_conversation.id = 123
        mock_conversation.user_id = 1

        # Mock database operations
        mock_session = mock_db.return_value
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = mock_conversation

        response = client.delete("/api/ai-editor/conversations/123")

        assert response.status_code == 200
        data = response.json()
        assert "Conversation deleted successfully" in data["message"]

        # Verify database operations were called
        mock_session.delete.assert_called_once_with(mock_conversation)
        mock_session.commit.assert_called_once()

    def test_edit_element_unauthorized(self, client):
        """Test editing element without authentication"""
        payload = {
            "element_type": "button",
            "current_text": "Click me",
            "edit_instruction": "Make it blue",
            "html_content": "<button>Click me</button>"
        }

        response = client.post("/api/ai-editor/edit-element", json=payload)

        assert response.status_code == 401

    @patch('routes.ai_editor.router.EditService')
    @patch('routes.ai_editor.router.get_current_user')
    def test_edit_element_success(self, mock_user, mock_edit_service, client):
        """Test successful element editing"""
        # Mock user
        mock_user.return_value.id = 1

        # Mock edit service
        mock_service_instance = mock_edit_service.return_value
        mock_response = AsyncMock()
        mock_response.html_content = "<button class='blue'>Click me</button>"
        mock_response.response = "Button updated"
        mock_response.status = "success"
        mock_service_instance.edit_element = AsyncMock(return_value=mock_response)

        payload = {
            "element_type": "button",
            "current_text": "Click me",
            "edit_instruction": "Make it blue",
            "html_content": "<button>Click me</button>"
        }

        response = client.post("/api/ai-editor/edit-element", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "blue" in data["html_content"]

    def test_status_endpoint(self, client):
        """Test status endpoint"""
        response = client.get("/api/ai-editor/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Editor working"
        assert "uptime" in data
        assert isinstance(data["uptime"], (int, float))

    def test_download_endpoint_not_implemented(self, client):
        """Test download endpoint returns not implemented"""
        response = client.get("/api/ai-editor/download/123")

        assert response.status_code == 501
        assert "not implemented" in response.json()["detail"].lower()

    def test_preview_endpoint_not_implemented(self, client):
        """Test preview endpoint returns not implemented"""
        response = client.get("/api/ai-editor/project/123/preview")

        assert response.status_code == 501
        assert "not implemented" in response.json()["detail"].lower()

    def test_preview_proxy_endpoint_not_implemented(self, client):
        """Test preview proxy endpoint returns not implemented"""
        response = client.get("/api/ai-editor/project/123/preview-proxy/somepath")

        assert response.status_code == 501
        assert "not implemented" in response.json()["detail"].lower()


class TestAIEditorEndpointIntegration:
    """Integration tests for the main AI editor endpoint"""

    @patch('routes.ai_editor.router.get_current_user')
    @patch('routes.ai_editor.router.ArchitectService')
    @patch('routes.ai_editor.router.DeveloperService')
    @patch('routes.ai_editor.router.CodeCombiner')
    def test_ai_editor_lite_mode_success(self, mock_combiner, mock_developer, mock_architect, mock_user, client):
        """Test successful AI editor request in lite mode"""
        # Mock user
        mock_user.return_value.id = 1

        # Mock services
        mock_architect_instance = mock_architect.return_value
        mock_developer_instance = mock_developer.return_value
        mock_combiner_instance = mock_combiner.return_value

        # Mock architect response
        mock_plan = AsyncMock()
        mock_plan.steps = []
        mock_plan.analysis = "Test analysis"
        mock_plan.final_structure = "Test structure"
        mock_architect_instance.create_plan = AsyncMock(return_value=mock_plan)

        # Mock developer response
        mock_code_part = AsyncMock()
        mock_code_part.type = "html"
        mock_code_part.code = "<div>Test</div>"
        mock_developer_instance.generate_code = AsyncMock(return_value=mock_code_part)

        # Mock combiner response
        mock_result = AsyncMock()
        mock_result.content = "<html><body>Test content</body></html>"
        mock_combiner_instance.combine_parts = AsyncMock(return_value=mock_result)

        payload = {
            "messages": [{"role": "user", "content": "Create a website"}],
            "mode": "lite",
            "use_two_stage": True
        }

        response = client.post("/api/ai-editor", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert data["status"] == "completed"
        assert "<html>" in data["content"]

    def test_ai_editor_invalid_request(self, client):
        """Test AI editor with invalid request (no messages)"""
        payload = {
            "messages": [],  # Empty messages should fail
            "mode": "lite"
        }

        response = client.post("/api/ai-editor", json=payload)

        assert response.status_code == 422  # Pydantic validation error

    @patch('routes.ai_editor.router.get_current_user')
    def test_ai_editor_unauthorized(self, mock_user, client):
        """Test AI editor without authentication"""
        payload = {
            "messages": [{"role": "user", "content": "Create a website"}],
            "mode": "lite"
        }

        response = client.post("/api/ai-editor", json=payload)

        assert response.status_code == 401





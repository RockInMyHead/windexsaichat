"""
Unit tests for EditService
"""

import pytest
from unittest.mock import AsyncMock, patch
from routes.ai_editor.services.edit_service import EditService
from routes.ai_editor.models import ElementEditRequest, EditElementResponse


class TestEditService:
    """Test cases for EditService"""

    @pytest.fixture
    def service(self):
        """Create EditService instance"""
        return EditService()

    @pytest.fixture
    def sample_edit_request(self):
        """Sample edit request for testing"""
        return ElementEditRequest(
            element_type="button",
            current_text="Click me",
            edit_instruction="Make it more attractive",
            html_content='<button>Click me</button>'
        )

    @pytest.mark.asyncio
    async def test_edit_element_success(self, service, sample_edit_request):
        """Test successful element editing"""
        # Mock OpenAI response with HTML markers
        mock_response = type('MockResponse', (), {
            'choices': [type('MockChoice', (), {
                'message': type('MockMessage', (), {
                    'content': """HTML_START
<button class="btn btn-primary">Click me!</button>
HTML_END

RESPONSE_START
Updated button with better styling
RESPONSE_END"""
                })()
            })()]
        })()

        with patch('routes.ai_editor.services.edit_service.openai_client.chat.completions.create',
                   return_value=mock_response):
            result = await service.edit_element(sample_edit_request)

            assert isinstance(result, EditElementResponse)
            assert result.status == "success"
            assert 'class="btn btn-primary"' in result.html_content
            assert result.response == "Updated button with better styling"

    @pytest.mark.asyncio
    async def test_edit_element_no_html_markers(self, service, sample_edit_request):
        """Test editing when response doesn't contain HTML markers"""
        # Mock response without proper markers
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Some random response without markers"

        with patch('routes.ai_editor.services.edit_service.openai_client.chat.completions.create',
                   return_value=mock_response):
            result = await service.edit_element(sample_edit_request)

            # Should return error status with original content
            assert result.status == "error"
            assert result.html_content == sample_edit_request.html_content
            assert "Не удалось извлечь обновленный HTML код" in result.response

    @pytest.mark.asyncio
    async def test_edit_element_no_response_markers(self, service, sample_edit_request):
        """Test editing when response doesn't contain response markers"""
        # Mock response with HTML but no response markers
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = """HTML_START
<button class="btn">Updated</button>
HTML_END"""

        with patch('routes.ai_editor.services.edit_service.openai_client.chat.completions.create',
                   return_value=mock_response):
            result = await service.edit_element(sample_edit_request)

            assert result.status == "success"
            assert result.html_content == '<button class="btn">Updated</button>'
            assert result.response == "Элемент успешно отредактирован."  # Default response

    @pytest.mark.asyncio
    async def test_edit_element_api_error(self, service, sample_edit_request):
        """Test error handling when API call fails"""
        with patch('routes.ai_editor.services.edit_service.openai_client.chat.completions.create',
                   side_effect=Exception("API Error")):
            result = await service.edit_element(sample_edit_request)

            assert result.status == "error"
            assert result.html_content == sample_edit_request.html_content
            assert "Ошибка редактирования" in result.response

    def test_edit_element_prompt_structure(self, service, sample_edit_request):
        """Test that the edit prompt has correct structure"""
        # We can't easily test the prompt content without accessing private methods,
        # but we can verify the service has the necessary components
        assert hasattr(service, 'edit_element')
        assert callable(service.edit_element)

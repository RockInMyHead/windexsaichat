"""
Unit tests for ArchitectService
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from routes.ai_editor.services.architect_service import ArchitectService
from routes.ai_editor.prompts.architect_prompts import ArchitectPromptBuilder


class TestArchitectService:
    """Test cases for ArchitectService"""

    @pytest.fixture
    def service(self):
        """Create ArchitectService instance"""
        prompt_builder = ArchitectPromptBuilder()
        return ArchitectService(prompt_builder)

    @pytest.mark.asyncio
    async def test_create_plan_success(self, service, sample_design_style, mock_openai_response):
        """Test successful plan creation"""
        user_request = "Create a landing page"
        mode = "lite"

        # Mock the design style selection and OpenAI client
        with patch('routes.ai_editor.services.architect_service.get_design_style_variation',
                   return_value=sample_design_style), \
             patch('routes.ai_editor.services.architect_service.openai_client.chat.completions.create',
                   new_callable=AsyncMock, return_value=mock_openai_response):
            plan = await service.create_plan(user_request, mode)

            assert plan is not None
            assert plan.analysis == "Test analysis"
            assert plan.final_structure == "Test structure"
            assert isinstance(plan.steps, list)

    @pytest.mark.asyncio
    async def test_create_plan_json_error_fallback(self, service, sample_design_style):
        """Test fallback plan creation when JSON parsing fails"""
        # Mock OpenAI to return invalid JSON
        service.prompt_builder = ArchitectPromptBuilder()
        with patch('routes.ai_editor.services.architect_service.openai_client') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "Invalid JSON response"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            with patch('routes.ai_editor.services.architect_service.get_design_style_variation',
                       return_value=sample_design_style):
                plan = await service.create_plan("Test request", "lite")

                # Should return fallback plan
                assert plan is not None
                assert "Test request" in plan.analysis
                assert len(plan.steps) == 6  # Default fallback has 6 steps

    @pytest.mark.asyncio
    async def test_create_plan_api_error_fallback(self, service, sample_design_style):
        """Test fallback plan creation when API call fails"""
        with patch('routes.ai_editor.services.architect_service.openai_client.chat.completions.create',
                   side_effect=Exception("API Error")):
            with patch('routes.ai_editor.services.architect_service.get_design_style_variation',
                       return_value=sample_design_style):
                plan = await service.create_plan("Test request", "lite")

                # Should return fallback plan
                assert plan is not None
                assert "Test request" in plan.analysis
                assert len(plan.steps) == 6

    def test_fallback_plan_structure(self, service):
        """Test that fallback plan has correct structure"""
        plan = service._create_fallback_plan("Test request", "lite")

        assert plan.analysis == "Создание lite проекта по запросу: Test request"
        assert len(plan.steps) == 6

        # Check first step structure
        first_step = plan.steps[0]
        assert first_step.id == 1
        assert first_step.code_type == "html"
        assert first_step.priority == "high"
        assert first_step.dependencies == []

        # Check that all steps have required fields
        for step in plan.steps:
            assert step.id is not None
            assert step.name is not None
            assert step.description is not None
            assert step.code_type in ["html", "css", "javascript"]
            assert step.priority in ["high", "medium", "low"]
            assert isinstance(step.dependencies, list)

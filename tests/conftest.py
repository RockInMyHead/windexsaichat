"""
Pytest configuration and fixtures for AI Editor tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Import the main app
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI response for testing"""
    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockChoice:
        def __init__(self, content):
            self.message = MockMessage(content)

    class MockResponse:
        def __init__(self, content='{"analysis": "Test analysis", "steps": [], "final_structure": "Test structure"}'):
            self.choices = [MockChoice(content)]

    return MockResponse()


@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    return mock_session


@pytest.fixture
def sample_design_style():
    """Sample design style for testing"""
    from routes.ai_editor.models import DesignStyle
    return DesignStyle(
        name="Test Style",
        colors=["#000000", "#ffffff"],
        gradients=["linear-gradient(45deg, #000000, #ffffff)"],
        effects=["test effect"]
    )


@pytest.fixture
def sample_plan_step():
    """Sample plan step for testing"""
    from routes.ai_editor.models import PlanStep
    return PlanStep(
        id=1,
        name="Test Step",
        description="Test description",
        code_type="html",
        priority="high",
        dependencies=[]
    )


@pytest.fixture
def sample_architect_plan(sample_plan_step):
    """Sample architect plan for testing"""
    from routes.ai_editor.models import ArchitectPlan
    return ArchitectPlan(
        analysis="Test analysis",
        steps=[sample_plan_step],
        final_structure="Test structure"
    )

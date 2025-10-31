"""
Pytest configuration and fixtures for WindexAI tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

# Import the refactored app
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main_refactored import app
from core.database import Base, get_db
from config import settings


@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()

    # Override settings for testing
    test_settings = settings.model_copy()
    test_settings.database_url = f"sqlite:///{db_path}"

    # Create test engine
    engine = create_engine(test_settings.database_url, connect_args={"check_same_thread": False})

    # Import models to ensure they're registered with Base
    from database import Base as AppBase
    from core.database import Base as CoreBase

    # Create tables from both Base instances
    AppBase.metadata.create_all(bind=engine)
    CoreBase.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    try:
        yield TestingSessionLocal
    finally:
        os.close(db_fd)
        os.unlink(db_path)


@pytest.fixture
def db_session(test_db):
    """Database session for testing"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


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

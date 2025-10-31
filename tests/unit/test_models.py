"""
Unit tests for Pydantic models
"""

import pytest
from routes.ai_editor.models import (
    DesignStyle,
    PlanStep,
    ArchitectPlan,
    CodePart,
    CombinedCodeResult,
    AIEditorRequest,
    AIEditorResponse,
    ElementEditRequest,
    EditElementResponse,
    ConversationSummary,
    ConversationDetail,
    ConversationDetailResponse,
    StatusResponse,
)


class TestDesignModels:
    """Test cases for design-related models"""

    def test_design_style_creation(self):
        """Test DesignStyle model creation"""
        style = DesignStyle(
            name="Test Style",
            colors=["#000000", "#ffffff"],
            gradients=["linear-gradient(45deg, #000000, #ffffff)"],
            effects=["shadow", "glow"]
        )

        assert style.name == "Test Style"
        assert len(style.colors) == 2
        assert len(style.gradients) == 1
        assert len(style.effects) == 2

    def test_plan_step_creation(self):
        """Test PlanStep model creation"""
        step = PlanStep(
            id=1,
            name="Test Step",
            description="Test description",
            code_type="html",
            priority="high",
            dependencies=[0]
        )

        assert step.id == 1
        assert step.name == "Test Step"
        assert step.code_type == "html"
        assert step.priority == "high"
        assert step.dependencies == [0]

    def test_architect_plan_creation(self):
        """Test ArchitectPlan model creation"""
        steps = [
            PlanStep(id=1, name="Step 1", description="Desc 1", code_type="html",
                    priority="high", dependencies=[]),
            PlanStep(id=2, name="Step 2", description="Desc 2", code_type="css",
                    priority="medium", dependencies=[1])
        ]

        plan = ArchitectPlan(
            analysis="Test analysis",
            steps=steps,
            final_structure="Test structure"
        )

        assert plan.analysis == "Test analysis"
        assert len(plan.steps) == 2
        assert plan.final_structure == "Test structure"
        assert plan.steps[1].dependencies == [1]


class TestCodeModels:
    """Test cases for code-related models"""

    def test_code_part_creation(self):
        """Test CodePart model creation"""
        part = CodePart(
            type="html",
            code="<div>Test</div>",
            step_name="Test Step"
        )

        assert part.type == "html"
        assert part.code == "<div>Test</div>"
        assert part.step_name == "Test Step"

    def test_combined_code_result_creation(self):
        """Test CombinedCodeResult model creation"""
        result = CombinedCodeResult(
            content="<html><body>Test</body></html>",
            parts_count=3,
            total_length=42
        )

        assert result.parts_count == 3
        assert result.total_length == 42
        assert "<html>" in result.content


class TestRequestResponseModels:
    """Test cases for API request/response models"""

    def test_ai_editor_request_creation(self):
        """Test AIEditorRequest model creation"""
        request = AIEditorRequest(
            messages=[{"role": "user", "content": "Create a website"}],
            model="gpt-4o-mini",
            conversation_id=123,
            mode="lite",
            use_two_stage=True
        )

        assert len(request.messages) == 1
        assert request.model == "gpt-4o-mini"
        assert request.conversation_id == 123
        assert request.mode == "lite"
        assert request.use_two_stage is True

    def test_ai_editor_response_creation(self):
        """Test AIEditorResponse model creation"""
        response = AIEditorResponse(
            content="<html>Test</html>",
            conversation_id=123,
            status="completed",
            timestamp="2023-01-01T00:00:00"
        )

        assert response.content == "<html>Test</html>"
        assert response.conversation_id == 123
        assert response.status == "completed"
        assert response.timestamp == "2023-01-01T00:00:00"

    def test_element_edit_request_creation(self):
        """Test ElementEditRequest model creation"""
        request = ElementEditRequest(
            element_type="button",
            current_text="Click me",
            edit_instruction="Make it blue",
            html_content="<button>Click me</button>"
        )

        assert request.element_type == "button"
        assert request.current_text == "Click me"
        assert request.edit_instruction == "Make it blue"
        assert "<button>" in request.html_content

    def test_edit_element_response_creation(self):
        """Test EditElementResponse model creation"""
        response = EditElementResponse(
            html_content="<button class='blue'>Click me</button>",
            response="Button updated successfully",
            status="success"
        )

        assert "class='blue'" in response.html_content
        assert response.response == "Button updated successfully"
        assert response.status == "success"


class TestConversationModels:
    """Test cases for conversation-related models"""

    def test_conversation_summary_creation(self):
        """Test ConversationSummary model creation"""
        summary = ConversationSummary(
            id=123,
            title="Test Conversation",
            date="2023-01-01T00:00:00",
            message_count=5
        )

        assert summary.id == 123
        assert summary.title == "Test Conversation"
        assert summary.message_count == 5

    def test_conversation_detail_creation(self):
        """Test ConversationDetail model creation"""
        from routes.ai_editor.models import MessageInfo

        messages = [
            MessageInfo(role="user", content="Hello", timestamp="2023-01-01T00:00:00"),
            MessageInfo(role="assistant", content="Hi!", timestamp="2023-01-01T00:00:01")
        ]

        detail = ConversationDetail(
            id=123,
            title="Test Conversation",
            created_at="2023-01-01T00:00:00",
            messages=messages
        )

        assert detail.id == 123
        assert len(detail.messages) == 2
        assert detail.messages[0].role == "user"

    def test_status_response_creation(self):
        """Test StatusResponse model creation"""
        response = StatusResponse(
            status="working",
            uptime=123.45,
            total_conversations=10,
            total_messages=50
        )

        assert response.status == "working"
        assert response.uptime == 123.45
        assert response.total_conversations == 10
        assert response.total_messages == 50


class TestModelValidation:
    """Test cases for model validation"""

    def test_invalid_code_type(self):
        """Test validation of invalid code type"""
        with pytest.raises(ValueError):
            PlanStep(
                id=1,
                name="Test",
                description="Test",
                code_type="invalid",  # Should be html, css, or javascript
                priority="high",
                dependencies=[]
            )

    def test_invalid_priority(self):
        """Test validation of invalid priority"""
        with pytest.raises(ValueError):
            PlanStep(
                id=1,
                name="Test",
                description="Test",
                code_type="html",
                priority="invalid",  # Should be high, medium, or low
                dependencies=[]
            )

    def test_empty_messages_validation(self):
        """Test validation of empty messages in AIEditorRequest"""
        with pytest.raises(ValueError):
            AIEditorRequest(
                messages=[],  # Should not be empty
                mode="lite"
            )

    def test_required_fields(self):
        """Test that required fields are enforced"""
        with pytest.raises(ValueError):
            DesignStyle(
                # Missing required 'name' field
                colors=["#000"],
                gradients=[],
                effects=[]
            )

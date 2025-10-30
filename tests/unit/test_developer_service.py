"""
Unit tests for DeveloperService
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from routes.ai_editor.services.developer_service import DeveloperService
from routes.ai_editor.prompts.developer_prompts import DeveloperPromptBuilder


class TestDeveloperService:
    """Test cases for DeveloperService"""

    @pytest.fixture
    def service(self):
        """Create DeveloperService instance"""
        prompt_builder = DeveloperPromptBuilder()
        return DeveloperService(prompt_builder)

    @pytest.mark.asyncio
    async def test_generate_code_success(self, service, sample_plan_step):
        """Test successful code generation"""
        # Setup mock response with clean code
        mock_response = type('MockResponse', (), {
            'choices': [type('MockChoice', (), {
                'message': type('MockMessage', (), {
                    'content': '<div>Test HTML</div>'
                })()
            })()]
        })()

        with patch('routes.ai_editor.services.developer_service.openai_client.chat.completions.create',
                   new_callable=AsyncMock, return_value=mock_response):
            result = await service.generate_code(sample_plan_step, "lite")

            assert result is not None
            assert result.type == "html"
            assert result.code == '<div>Test HTML</div>'
            assert result.step_name == "Test Step"

    @pytest.mark.asyncio
    async def test_generate_code_with_markdown_cleanup(self, service, sample_plan_step):
        """Test code generation with markdown formatting cleanup"""
        # Setup mock response with markdown formatting
        mock_response = type('MockResponse', (), {
            'choices': [type('MockChoice', (), {
                'message': type('MockMessage', (), {
                    'content': '''```html
<div>Test HTML</div>
```'''
                })()
            })()]
        })()

        with patch('routes.ai_editor.services.developer_service.openai_client.chat.completions.create',
                   new_callable=AsyncMock, return_value=mock_response):
            result = await service.generate_code(sample_plan_step, "lite")

            assert result.code == '<div>Test HTML</div>'  # Markdown should be cleaned

    @pytest.mark.asyncio
    async def test_generate_code_api_error(self, service, sample_plan_step):
        """Test error handling when API call fails"""
        with patch('routes.ai_editor.services.developer_service.openai_client.chat.completions.create',
                   side_effect=Exception("API Error")):
            result = await service.generate_code(sample_plan_step, "lite")

            # Should return error fallback
            assert result.type == "html"
            assert result.step_name == "Test Step"
            assert "<!-- Error generating html code -->" in result.code

    def test_clean_markdown_formatting_html(self, service):
        """Test markdown cleanup for HTML"""
        code = '''```html
<div>Test</div>
```
```html
<span>More</span>
```'''

        result = service._clean_markdown_formatting(code, "html")
        assert result == '<div>Test</div>\n<span>More</span>'

    def test_clean_markdown_formatting_css(self, service):
        """Test markdown cleanup for CSS"""
        code = '''```css
.test { color: red; }
```
```css
.another { color: blue; }
```'''

        result = service._clean_markdown_formatting(code, "css")
        assert result == '.test { color: red; }\n.another { color: blue; }'

    def test_clean_markdown_formatting_javascript(self, service):
        """Test markdown cleanup for JavaScript"""
        code = '''```javascript
function test() { return true; }
```
```js
const x = 1;
```'''

        result = service._clean_markdown_formatting(code, "javascript")
        assert result == 'function test() { return true; }\nconst x = 1;'

    def test_get_error_fallback_html(self, service):
        """Test error fallback for HTML"""
        result = service._get_error_fallback("html", "Test Step")

        assert result.type == "html"
        assert result.step_name == "Test Step"
        assert "<!-- Error generating html code -->" in result.code

    def test_get_error_fallback_css(self, service):
        """Test error fallback for CSS"""
        result = service._get_error_fallback("css", "Test Step")

        assert result.type == "css"
        assert result.step_name == "Test Step"
        assert "/* Error generating css code */" in result.code

    def test_get_error_fallback_javascript(self, service):
        """Test error fallback for JavaScript"""
        result = service._get_error_fallback("javascript", "Test Step")

        assert result.type == "javascript"
        assert result.step_name == "Test Step"
        assert "// Error generating javascript code" in result.code

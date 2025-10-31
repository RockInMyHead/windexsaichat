"""
Unit tests for utility functions
"""

import pytest
from routes.ai_editor.utils.html_parser import extract_from_html
from routes.ai_editor.utils.search_utils import should_search_web, extract_search_query


class TestHTMLParser:
    """Test cases for HTML parser utilities"""

    def test_extract_from_html_simple(self):
        """Test extracting from simple HTML"""
        html = "<div>Hello World</div>"
        result = extract_from_html(html)

        assert result["body"] == "<div>Hello World</div>"
        assert result["styles"] == ""
        assert result["scripts"] == ""

    def test_extract_from_html_with_styles(self):
        """Test extracting HTML with embedded styles"""
        html = """
        <html>
        <head>
        <style>
        .test { color: red; }
        </style>
        </head>
        <body>
        <div>Hello</div>
        </body>
        </html>
        """
        result = extract_from_html(html)

        assert "<div>Hello</div>" in result["body"]
        assert ".test { color: red; }" in result["styles"]
        assert result["scripts"] == ""

    def test_extract_from_html_with_scripts(self):
        """Test extracting HTML with embedded scripts"""
        html = """
        <html>
        <body>
        <div>Hello</div>
        <script>
        console.log('test');
        </script>
        </body>
        </html>
        """
        result = extract_from_html(html)

        assert "<div>Hello</div>" in result["body"]
        assert "console.log('test');" in result["scripts"]
        assert result["styles"] == ""

    def test_extract_from_html_full_document(self):
        """Test extracting from full HTML document"""
        html = """<!DOCTYPE html>
        <html>
        <head>
        <title>Test</title>
        <style>body { margin: 0; }</style>
        </head>
        <body>
        <h1>Hello</h1>
        <script>alert('test');</script>
        </body>
        </html>"""
        result = extract_from_html(html)

        assert "<h1>Hello</h1>" in result["body"]
        assert "body { margin: 0; }" in result["styles"]
        assert "alert('test');" in result["scripts"]

    def test_extract_from_html_empty(self):
        """Test extracting from empty HTML"""
        result = extract_from_html("")

        assert result["body"] == ""
        assert result["styles"] == ""
        assert result["scripts"] == ""

    def test_extract_from_html_no_body(self):
        """Test extracting HTML without body tag"""
        html = "<div>Content without body</div>"
        result = extract_from_html(html)

        assert result["body"] == "<div>Content without body</div>"
        assert result["styles"] == ""
        assert result["scripts"] == ""

    def test_extract_from_html_multiple_styles_scripts(self):
        """Test extracting HTML with multiple styles and scripts"""
        html = """
        <style>.class1 { color: red; }</style>
        <div>Content</div>
        <style>.class2 { color: blue; }</style>
        <script>func1();</script>
        <script>func2();</script>
        """
        result = extract_from_html(html)

        assert ".class1 { color: red; }" in result["styles"]
        assert ".class2 { color: blue; }" in result["styles"]
        assert "func1();" in result["scripts"]
        assert "func2();" in result["scripts"]
        assert "<div>Content</div>" in result["body"]


class TestSearchUtils:
    """Test cases for search utility functions"""

    @pytest.mark.parametrize("message,expected", [
        ("найди информацию о Python", True),
        ("поищи последние новости", True),
        ("актуальные данные по курсу", True),
        ("что происходит в мире", True),
        ("статистика продаж", True),
        ("расскажи о компании", False),
        ("создай веб-сайт", False),
        ("привет", False),
    ])
    def test_should_search_web(self, message, expected):
        """Test should_search_web function with various inputs"""
        assert should_search_web(message) == expected

    def test_extract_search_query(self):
        """Test extract_search_query function"""
        message = "найди информацию о Python"
        result = extract_search_query(message)

        # Currently just returns the message as-is
        assert result == message

    def test_should_search_web_case_insensitive(self):
        """Test that should_search_web is case insensitive"""
        assert should_search_web("НАЙДИ информацию")
        assert should_search_web("Поищи данные")
        assert should_search_web("АКТУАЛЬНЫЕ новости")

    def test_should_search_web_empty_message(self):
        """Test should_search_web with empty message"""
        assert not should_search_web("")

    def test_should_search_web_only_keywords(self):
        """Test should_search_web with message containing only keywords"""
        assert should_search_web("найди")
        assert should_search_web("поиск")
        assert should_search_web("новости")






"""
Unit tests for Core.utils.text_parsers module.
Tests JSON extraction, code extraction, and validation functions.
"""
import pytest
from Core.utils.text_parsers import (
    extract_json,
    extract_code,
    validate_python_syntax,
    clean_response
)


class TestExtractJson:
    """Tests for extract_json function."""

    def test_extract_simple_json_list(self):
        """Test extraction of a simple JSON list."""
        text = 'Here is the list: [{"name": "test", "value": 123}]'
        result = extract_json(text)
        assert result == [{"name": "test", "value": 123}]

    def test_extract_nested_json(self):
        """Test extraction of nested JSON structures."""
        text = '''
        Output:
        [
            {
                "file": "main.py",
                "data": {"lines": 10}
            }
        ]
        '''
        result = extract_json(text)
        assert len(result) == 1
        assert result[0]["file"] == "main.py"
        assert result[0]["data"]["lines"] == 10

    def test_extract_json_with_multiple_brackets(self):
        """Test JSON extraction with complex bracket nesting."""
        text = 'Before [{"key": [1, 2, 3]}] after'
        result = extract_json(text)
        assert result == [{"key": [1, 2, 3]}]

    def test_extract_json_not_found(self):
        """Test when no JSON list is present."""
        text = "This is just plain text with no JSON"
        result = extract_json(text)
        assert result is None

    def test_extract_json_with_text_before_and_after(self):
        """Test JSON extraction with surrounding text."""
        text = '''
        Here's some explanation.
        [{"id": 1}, {"id": 2}]
        And some more text after.
        '''
        result = extract_json(text)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    def test_extract_json_empty_list(self):
        """Test extraction of empty JSON list."""
        text = "Result: []"
        result = extract_json(text)
        assert result == []

    def test_extract_json_malformed(self):
        """Test handling of malformed JSON."""
        text = '[{"key": "value",}]'  # Trailing comma
        result = extract_json(text)
        # Should return None for malformed JSON
        assert result is None


class TestExtractCode:
    """Tests for extract_code function."""

    def test_extract_code_from_markdown_python(self):
        """Test extraction of Python code from markdown block."""
        text = '''
        Here's the code:
        ```python
        def hello():
            print("Hello, World!")
        ```
        '''
        result = extract_code(text)
        assert "def hello():" in result
        assert 'print("Hello, World!")' in result

    def test_extract_code_without_language_specifier(self):
        """Test extraction from code block without language."""
        text = '''
        ```
        x = 10
        y = 20
        ```
        '''
        result = extract_code(text)
        assert "x = 10" in result
        assert "y = 20" in result

    def test_extract_code_multiple_blocks(self):
        """Test that only first code block is extracted."""
        text = '''
        ```python
        # Block 1
        x = 1
        ```
        
        ```python
        # Block 2
        y = 2
        ```
        '''
        result = extract_code(text)
        assert "Block 1" in result
        assert "x = 1" in result
        # Should only get first block
        assert "Block 2" not in result

    def test_extract_code_no_code_block(self):
        """Test when no code block is present."""
        text = "This is just plain text"
        result = extract_code(text)
        # Should return None when no code block found
        assert result is None

    def test_extract_code_preserves_indentation(self):
        """Test that code indentation is preserved."""
        text = '''
        ```python
        class MyClass:
            def __init__(self):
                self.value = 42
        ```
        '''
        result = extract_code(text)
        assert "class MyClass:" in result
        assert "    def __init__(self):" in result
        assert "        self.value = 42" in result

    def test_extract_code_with_blank_lines(self):
        """Test extraction preserves blank lines."""
        text = '''
        ```python
        def func1():
            pass

        def func2():
            pass
        ```
        '''
        result = extract_code(text)
        assert result.count('\n\n') >= 1


class TestValidatePythonSyntax:
    """Tests for validate_python_syntax function."""

    def test_valid_simple_code(self):
        """Test validation of simple valid Python code."""
        code = "x = 10\nprint(x)"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_function_definition(self):
        """Test validation of function definition."""
        code = '''
def greet(name):
    return f"Hello, {name}!"
'''
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_class_definition(self):
        """Test validation of class definition."""
        code = '''
class Calculator:
    def add(self, a, b):
        return a + b
'''
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_invalid_syntax_error(self):
        """Test detection of syntax error."""
        code = "def broken(\nprint('missing closing paren')"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert error is not None
        # Error message should contain "syntax" or "error"
        assert "syntax" in error.lower() or "error" in error.lower()

    def test_invalid_indentation_error(self):
        """Test detection of indentation error."""
        code = '''
def test():
print("bad indent")
'''
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "IndentationError" in error or "expected an indented block" in error.lower()

    def test_empty_code(self):
        """Test validation of empty code."""
        code = ""
        is_valid, error = validate_python_syntax(code)
        # Empty code should be valid (no syntax errors)
        assert is_valid is True

    def test_code_with_comments_only(self):
        """Test validation of code with only comments."""
        code = "# This is a comment\n# Another comment"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True

    def test_invalid_unclosed_string(self):
        """Test detection of unclosed string."""
        code = 'message = "Hello, World!'
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert error is not None


class TestCleanResponse:
    """Tests for clean_response function."""

    def test_clean_simple_text(self):
        """Test cleaning of simple text."""
        text = "This is a response"
        result = clean_response(text)
        assert result == "This is a response"

    def test_clean_with_whitespace(self):
        """Test removal of extra whitespace."""
        text = "  \n  Response with whitespace  \n  "
        result = clean_response(text)
        assert result == "Response with whitespace"

    def test_clean_empty_string(self):
        """Test cleaning empty string."""
        text = "   \n  \n   "
        result = clean_response(text)
        assert result == ""

    def test_clean_preserves_internal_whitespace(self):
        """Test that internal whitespace is preserved."""
        text = "Line 1\nLine 2\n  Indented line"
        result = clean_response(text)
        assert "Line 1\nLine 2" in result
        # Should preserve structure

    def test_clean_with_code_blocks(self):
        """Test cleaning response with code blocks."""
        text = '''
        Here is code:
        ```python
        def test():
            pass
        ```
        '''
        result = clean_response(text)
        assert "```python" in result
        # Structure should be maintained


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_extract_json_with_unicode(self):
        """Test JSON extraction with unicode characters."""
        text = '[{"name": "Test™", "emoji": "🎉"}]'
        result = extract_json(text)
        assert result is not None
        assert result[0]["name"] == "Test™"
        assert result[0]["emoji"] == "🎉"

    def test_extract_code_with_special_chars(self):
        """Test code extraction with special characters."""
        text = '''
        ```python
        # Test special chars: <>&"'
        msg = "Special: <>&\\"\\\'"
        ```
        '''
        result = extract_code(text)
        assert "Special:" in result

    def test_validate_python_with_long_lines(self):
        """Test validation with very long lines."""
        code = "x = " + "1" * 1000  # Very long line
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True

    def test_large_json_extraction(self):
        """Test extraction of large JSON structure."""
        large_list = [{"id": i, "value": f"item_{i}"} for i in range(100)]
        import json
        text = f"Result: {json.dumps(large_list)}"
        result = extract_json(text)
        assert len(result) == 100
        assert result[0]["id"] == 0
        assert result[99]["id"] == 99


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

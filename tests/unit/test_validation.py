"""
Unit tests for Core.utils.validation module.
Tests validation functions with detailed error messages.
"""
import pytest
from Core.utils.validation import (
    ValidationResult,
    validate_architect_output,
    validate_planner_output,
    validate_developer_output,
    validate_task_description,
    validate_project_name,
    validate_agent_context,
    validate_file_path
)


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_valid_result(self):
        """Test valid result with no errors."""
        result = ValidationResult(True)
        assert result.valid is True
        assert bool(result) is True
        assert result.errors == []
        assert result.warnings == []

    def test_invalid_result_with_errors(self):
        """Test invalid result with errors."""
        errors = ["Error 1", "Error 2"]
        result = ValidationResult(False, errors=errors)
        assert result.valid is False
        assert bool(result) is False
        assert len(result.errors) == 2

    def test_valid_with_warnings(self):
        """Test valid result can have warnings."""
        warnings = ["Warning 1"]
        result = ValidationResult(True, warnings=warnings)
        assert result.valid is True
        assert len(result.warnings) == 1

    def test_get_summary(self):
        """Test summary generation."""
        errors = ["Error 1"]
        warnings = ["Warning 1"]
        result = ValidationResult(False, errors=errors, warnings=warnings)
        summary = result.get_summary()
        assert "Errors" in summary
        assert "Warnings" in summary


class TestValidateArchitectOutput:
    """Tests for validate_architect_output function."""

    def test_valid_architect_output(self):
        """Test with valid architect output."""
        file_list = [
            {
                "path": "main.py",
                "type": "python",
                "action": "create",
                "description": "Main file"
            }
        ]
        result = validate_architect_output(file_list)
        assert result.valid is True

    def test_empty_list(self):
        """Test with empty file list."""
        result = validate_architect_output([])
        assert result.valid is True  # Empty is valid but has warning
        assert len(result.warnings) > 0

    def test_not_a_list(self):
        """Test with non-list input."""
        result = validate_architect_output("not a list")
        assert result.valid is False
        assert any("list" in e.lower() for e in result.errors)

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        file_list = [{"path": "main.py"}]  # Missing type and action
        result = validate_architect_output(file_list)
        assert result.valid is False
        assert any("missing" in e.lower() for e in result.errors)

    def test_invalid_action(self):
        """Test with invalid action."""
        file_list = [{
            "path": "main.py",
            "type": "python",
            "action": "invalid_action"
        }]
        result = validate_architect_output(file_list)
        assert result.valid is False
        assert any("action" in e.lower() for e in result.errors)

    def test_unsafe_path_with_dotdot(self):
        """Test path with .. generates warning."""
        file_list = [{
            "path": "../dangerous/path.py",
            "type": "python",
            "action": "create"
        }]
        result = validate_architect_output(file_list)
        # May be valid but should have warning
        assert len(result.warnings) > 0

    def test_absolute_path_warning(self):
        """Test absolute path generates warning."""
        file_list = [{
            "path": "/absolute/path.py",
            "type": "python",
            "action": "create"
        }]
        result = validate_architect_output(file_list)
        assert len(result.warnings) > 0


class TestValidatePlannerOutput:
    """Tests for validate_planner_output function."""

    def test_valid_plan(self):
        """Test with valid plan."""
        plan = """
        1. Create main function
        2. Implement helper functions
        3. Add error handling
        """
        result = validate_planner_output(plan)
        assert result.valid is True

    def test_empty_plan(self):
        """Test with empty plan."""
        result = validate_planner_output("")
        assert result.valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_not_a_string(self):
        """Test with non-string input."""
        result = validate_planner_output(["list", "of", "items"])
        assert result.valid is False
        assert any("string" in e.lower() for e in result.errors)

    def test_very_short_plan(self):
        """Test short plan generates warning."""
        result = validate_planner_output("Do something")
        # Valid but should have warning
        assert len(result.warnings) > 0

    def test_plan_with_structure(self):
        """Test plan with clear structure."""
        plan = "Step 1: Create function\nStep 2: Implement logic"
        result = validate_planner_output(plan)
        assert result.valid is True


class TestValidateDeveloperOutput:
    """Tests for validate_developer_output function."""

    def test_valid_python_code(self):
        """Test with valid Python code."""
        code = '''
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
'''
        result = validate_developer_output(code, "main.py")
        assert result.valid is True

    def test_empty_code(self):
        """Test with empty code."""
        result = validate_developer_output("")
        assert result.valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_not_a_string(self):
        """Test with non-string input."""
        result = validate_developer_output({"code": "test"})
        assert result.valid is False

    def test_very_short_code(self):
        """Test short code generates warning."""
        result = validate_developer_output("x = 1")
        # Valid but may have warning
        assert result.valid is True

    def test_python_file_without_imports(self):
        """Test Python file without imports may get warning."""
        code = "def test():\n    pass\n" * 20  # Long enough to trigger check
        result = validate_developer_output(code, "test.py")
        # May have warning about missing imports
        assert result.valid is True

    def test_python_file_without_functions(self):
        """Test Python file without functions/classes."""
        code = "x = 1\ny = 2\n" * 30  # Long enough
        result = validate_developer_output(code, "test.py")
        assert result.valid is True
        # May have warning


class TestValidateTaskDescription:
    """Tests for validate_task_description function."""

    def test_valid_task(self):
        """Test with valid task description."""
        result = validate_task_description("Create a calculator application with basic operations")
        assert result.valid is True

    def test_empty_task(self):
        """Test with empty task."""
        result = validate_task_description("")
        assert result.valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_short_task(self):
        """Test short task generates warning."""
        result = validate_task_description("Do task")
        # Valid but should have warning
        assert len(result.warnings) > 0

    def test_very_long_task(self):
        """Test very long task generates warning."""
        long_task = "Do something " * 200
        result = validate_task_description(long_task)
        assert len(result.warnings) > 0

    def test_question_format(self):
        """Test task as question generates warning."""
        result = validate_task_description("Can you create a calculator?")
        assert len(result.warnings) > 0

    def test_vague_language(self):
        """Test vague language generates warning."""
        result = validate_task_description("Create something that does stuff")
        assert len(result.warnings) > 0
        assert any("vague" in w.lower() for w in result.warnings)


class TestValidateProjectName:
    """Tests for validate_project_name function."""

    def test_valid_project_name(self):
        """Test with valid project name."""
        result = validate_project_name("my_calculator")
        assert result.valid is True

    def test_valid_with_hyphens(self):
        """Test valid name with hyphens."""
        result = validate_project_name("my-calculator-app")
        assert result.valid is True

    def test_empty_name(self):
        """Test with empty name."""
        result = validate_project_name("")
        assert result.valid is False

    def test_invalid_characters(self):
        """Test with invalid characters."""
        result = validate_project_name("my project!")
        assert result.valid is False
        assert any("invalid" in e.lower() for e in result.errors)

    def test_spaces_in_name(self):
        """Test spaces in name."""
        result = validate_project_name("my project")
        assert result.valid is False
        assert any("space" in e.lower() for e in result.errors)

    def test_starts_with_number(self):
        """Test name starting with number."""
        result = validate_project_name("123project")
        # Valid but should have warning
        assert len(result.warnings) > 0

    def test_very_short_name(self):
        """Test very short name."""
        result = validate_project_name("ab")
        assert len(result.warnings) > 0

    def test_very_long_name(self):
        """Test very long name."""
        result = validate_project_name("a" * 60)
        assert len(result.warnings) > 0

    def test_mixed_separators(self):
        """Test mixed hyphens and underscores."""
        result = validate_project_name("my_project-name")
        assert len(result.warnings) > 0


class TestValidateAgentContext:
    """Tests for validate_agent_context function."""

    def test_valid_context(self):
        """Test with valid context."""
        context = {"task": "test", "psi": "state"}
        result = validate_agent_context(context, ["task", "psi"])
        assert result.valid is True

    def test_missing_keys(self):
        """Test with missing required keys."""
        context = {"task": "test"}
        result = validate_agent_context(context, ["task", "psi"])
        assert result.valid is False
        assert any("missing" in e.lower() for e in result.errors)

    def test_not_a_dict(self):
        """Test with non-dict input."""
        result = validate_agent_context("not a dict", ["key"])
        assert result.valid is False

    def test_none_values(self):
        """Test with None values."""
        context = {"task": None}
        result = validate_agent_context(context, ["task"])
        assert result.valid is False
        assert any("none" in e.lower() for e in result.errors)

    def test_empty_string_values(self):
        """Test with empty string values."""
        context = {"task": ""}
        result = validate_agent_context(context, ["task"])
        assert result.valid is False


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def test_valid_relative_path(self):
        """Test with valid relative path."""
        result = validate_file_path("src/main.py")
        assert result.valid is True

    def test_empty_path(self):
        """Test with empty path."""
        result = validate_file_path("")
        assert result.valid is False

    def test_path_traversal(self):
        """Test path with .. (traversal attempt)."""
        result = validate_file_path("../dangerous.py")
        assert result.valid is False
        assert any("security" in e.lower() for e in result.errors)

    def test_absolute_path(self):
        """Test absolute path generates warning."""
        result = validate_file_path("/absolute/path.py")
        assert len(result.warnings) > 0

    def test_invalid_characters(self):
        """Test path with invalid characters."""
        result = validate_file_path("file<name>.py")
        assert result.valid is False

    def test_no_extension(self):
        """Test file without extension."""
        result = validate_file_path("README")
        assert len(result.warnings) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

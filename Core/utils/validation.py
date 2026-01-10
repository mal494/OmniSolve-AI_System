"""
Validation utilities for OmniSolve.
Provides comprehensive input validation with detailed error messages.
"""
from typing import Dict, List, Optional, Any, Tuple
import re
from pathlib import Path

from ..exceptions.errors import (
    CodeValidationError,
    ParsingError,
    ConfigurationError
)
from ..logging import get_logger

logger = get_logger('validation')


class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(self, valid: bool, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        """
        Initialize validation result.
        
        Args:
            valid: Whether validation passed
            errors: List of error messages
            warnings: List of warning messages
        """
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def __bool__(self) -> bool:
        """Return validity as boolean."""
        return self.valid
    
    def __str__(self) -> str:
        """String representation of validation result."""
        if self.valid:
            if self.warnings:
                return f"Valid (with {len(self.warnings)} warnings)"
            return "Valid"
        return f"Invalid: {len(self.errors)} errors"
    
    def get_summary(self) -> str:
        """Get detailed summary of validation result."""
        parts = []
        if self.errors:
            parts.append(f"Errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                parts.append(f"  {i}. {error}")
        if self.warnings:
            parts.append(f"Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                parts.append(f"  {i}. {warning}")
        return '\n'.join(parts) if parts else "No issues found"


def validate_architect_output(file_list: Any) -> ValidationResult:
    """
    Validate Architect agent output format.
    
    Args:
        file_list: Output from Architect agent
        
    Returns:
        ValidationResult with detailed feedback
    """
    errors = []
    warnings = []
    
    # Check if it's a list
    if not isinstance(file_list, list):
        errors.append(f"Expected list but got {type(file_list).__name__}")
        return ValidationResult(False, errors)
    
    # Check if empty
    if len(file_list) == 0:
        warnings.append("File list is empty - no files to generate")
    
    # Validate each file entry
    required_fields = {'path', 'type', 'action'}
    valid_actions = {'create', 'modify', 'preserve', 'delete'}
    
    for i, file_entry in enumerate(file_list):
        entry_prefix = f"File entry {i + 1}"
        
        # Check if it's a dictionary
        if not isinstance(file_entry, dict):
            errors.append(f"{entry_prefix}: Expected dict but got {type(file_entry).__name__}")
            continue
        
        # Check required fields
        missing_fields = required_fields - set(file_entry.keys())
        if missing_fields:
            errors.append(f"{entry_prefix}: Missing required fields: {', '.join(missing_fields)}")
        
        # Validate path
        if 'path' in file_entry:
            path = file_entry['path']
            if not path or not isinstance(path, str):
                errors.append(f"{entry_prefix}: Invalid path (must be non-empty string)")
            elif '..' in path:
                warnings.append(f"{entry_prefix}: Path contains '..' which may be unsafe: {path}")
            elif path.startswith('/'):
                warnings.append(f"{entry_prefix}: Absolute path used: {path}")
        
        # Validate action
        if 'action' in file_entry:
            action = file_entry['action']
            if action not in valid_actions:
                errors.append(
                    f"{entry_prefix}: Invalid action '{action}'. "
                    f"Must be one of: {', '.join(valid_actions)}"
                )
        
        # Validate type
        if 'type' in file_entry:
            file_type = file_entry['type']
            if not file_type or not isinstance(file_type, str):
                warnings.append(f"{entry_prefix}: File type should be a non-empty string")
    
    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings)


def validate_planner_output(plan: Any) -> ValidationResult:
    """
    Validate Planner agent output format.
    
    Args:
        plan: Output from Planner agent
        
    Returns:
        ValidationResult with detailed feedback
    """
    errors = []
    warnings = []
    
    # Check if it's a string
    if not isinstance(plan, str):
        errors.append(f"Plan must be a string, got {type(plan).__name__}")
        return ValidationResult(False, errors)
    
    # Check if empty
    if not plan.strip():
        errors.append("Plan is empty")
        return ValidationResult(False, errors)
    
    # Check minimum length (plans should have some substance)
    if len(plan.strip()) < 50:
        warnings.append(f"Plan is very short ({len(plan.strip())} chars) - may lack detail")
    
    # Check for common plan elements
    plan_lower = plan.lower()
    has_structure = any(keyword in plan_lower for keyword in [
        'step', 'function', 'class', 'method', 'implement', 'create', 'define'
    ])
    
    if not has_structure:
        warnings.append("Plan may lack clear structure or implementation steps")
    
    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings)


def validate_developer_output(code: Any, file_path: Optional[str] = None) -> ValidationResult:
    """
    Validate Developer agent output format and basic code quality.
    
    Args:
        code: Output from Developer agent
        file_path: Optional file path for context
        
    Returns:
        ValidationResult with detailed feedback
    """
    errors = []
    warnings = []
    
    # Check if it's a string
    if not isinstance(code, str):
        errors.append(f"Code must be a string, got {type(code).__name__}")
        return ValidationResult(False, errors)
    
    # Check if empty
    if not code.strip():
        errors.append("Code is empty")
        return ValidationResult(False, errors)
    
    # Check for minimum content
    if len(code.strip()) < 10:
        warnings.append("Code is very short - may be incomplete")
    
    # Python-specific validation (if file_path suggests Python)
    if file_path and file_path.endswith('.py'):
        # Check for common Python issues
        if 'import ' not in code and 'from ' not in code and len(code) > 100:
            warnings.append("No import statements found - code may be incomplete")
        
        # Check for basic structure
        if 'def ' not in code and 'class ' not in code and len(code) > 50:
            warnings.append("No functions or classes defined - may be incomplete")
        
        # Check indentation issues (basic)
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if line and not line[0].isspace() and line[0] != '#':
                # Check if line after def/class is indented
                if i < len(lines):
                    prev_line = lines[i - 1].strip()
                    if prev_line.endswith(':'):
                        next_line = lines[i] if i < len(lines) else ''
                        if next_line and not next_line[0].isspace():
                            warnings.append(f"Line {i + 1}: Expected indentation after '{prev_line}'")
    
    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings)


def validate_task_description(task: str) -> ValidationResult:
    """
    Validate user task description.
    
    Args:
        task: User's task description
        
    Returns:
        ValidationResult with detailed feedback
    """
    errors = []
    warnings = []
    
    # Check if empty
    if not task or not task.strip():
        errors.append("Task description is empty")
        return ValidationResult(False, errors)
    
    # Check minimum length
    if len(task.strip()) < 10:
        warnings.append("Task description is very short - may lack detail")
    
    # Check if too long
    if len(task) > 2000:
        warnings.append(f"Task description is very long ({len(task)} chars) - consider breaking into smaller tasks")
    
    # Check for common issues
    if task.strip().endswith('?'):
        warnings.append("Task is phrased as a question - rephrase as a directive for better results")
    
    # Check for vague language
    vague_terms = ['something', 'thing', 'stuff', 'maybe', 'kind of', 'sort of']
    task_lower = task.lower()
    found_vague = [term for term in vague_terms if term in task_lower]
    if found_vague:
        warnings.append(f"Task contains vague language: {', '.join(found_vague)} - be more specific")
    
    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings)


def validate_project_name(project_name: str) -> ValidationResult:
    """
    Validate project name follows conventions.
    
    Args:
        project_name: Name of the project
        
    Returns:
        ValidationResult with detailed feedback
    """
    errors = []
    warnings = []
    
    # Check if empty
    if not project_name or not project_name.strip():
        errors.append("Project name is empty")
        return ValidationResult(False, errors)
    
    # Check for invalid characters
    if not re.match(r'^[a-zA-Z0-9_-]+$', project_name):
        errors.append(
            "Project name contains invalid characters. "
            "Use only letters, numbers, underscores, and hyphens."
        )
    
    # Check if starts with number
    if project_name[0].isdigit():
        warnings.append("Project name starts with a number - may cause issues in some contexts")
    
    # Check length
    if len(project_name) < 3:
        warnings.append("Project name is very short - use a more descriptive name")
    
    if len(project_name) > 50:
        warnings.append("Project name is very long - consider using a shorter name")
    
    # Check for spaces (should be replaced with underscores or hyphens)
    if ' ' in project_name:
        errors.append("Project name contains spaces - use underscores or hyphens instead")
    
    # Check naming convention
    if '-' in project_name and '_' in project_name:
        warnings.append("Project name mixes hyphens and underscores - stick to one style")
    
    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings)


def validate_agent_context(context: Dict[str, Any], required_keys: List[str]) -> ValidationResult:
    """
    Validate that agent context contains required keys.
    
    Args:
        context: Context dictionary passed to agent
        required_keys: List of required keys
        
    Returns:
        ValidationResult with detailed feedback
    """
    errors = []
    warnings = []
    
    # Check if context is a dict
    if not isinstance(context, dict):
        errors.append(f"Context must be a dictionary, got {type(context).__name__}")
        return ValidationResult(False, errors)
    
    # Check required keys
    missing_keys = set(required_keys) - set(context.keys())
    if missing_keys:
        errors.append(f"Context missing required keys: {', '.join(missing_keys)}")
    
    # Check for empty values in required keys
    for key in required_keys:
        if key in context:
            value = context[key]
            if value is None:
                errors.append(f"Context key '{key}' is None")
            elif isinstance(value, str) and not value.strip():
                errors.append(f"Context key '{key}' is empty string")
    
    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings)


def validate_file_path(file_path: str, project_root: Optional[Path] = None) -> ValidationResult:
    """
    Validate file path for security and correctness.
    
    Args:
        file_path: Path to validate
        project_root: Optional project root for relative path validation
        
    Returns:
        ValidationResult with detailed feedback
    """
    errors = []
    warnings = []
    
    # Check if empty
    if not file_path or not file_path.strip():
        errors.append("File path is empty")
        return ValidationResult(False, errors)
    
    # Check for path traversal attempts
    if '..' in file_path:
        errors.append("File path contains '..' which may be a security risk")
    
    # Check for absolute paths
    if file_path.startswith('/') or (len(file_path) > 1 and file_path[1] == ':'):
        warnings.append("File path is absolute - relative paths are recommended")
    
    # Check for invalid characters
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
    found_invalid = [char for char in invalid_chars if char in file_path]
    if found_invalid:
        errors.append(f"File path contains invalid characters: {', '.join(found_invalid)}")
    
    # Check file extension
    if '.' not in Path(file_path).name:
        warnings.append("File has no extension - may cause issues")
    
    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings)

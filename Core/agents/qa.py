"""
QA agent - Reviews and validates generated code.
"""
from typing import Dict, Any, Optional, Tuple

from ..brain import BrainAPI
from .base_agent import BaseAgent
from ..utils.text_parsers import validate_python_syntax
from ..exceptions.errors import CodeValidationError


class QAAgent(BaseAgent):
    """
    QA agent responsible for reviewing and validating code.
    Checks for syntax errors, logic issues, and best practices.
    """

    def __init__(self, brain: Optional[BrainAPI] = None):
        """Initialize the QA agent."""
        super().__init__("QA", brain=brain)

    def process(self, task: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Review code and determine if it passes quality checks.

        Args:
            task: The review request (usually just the code)
            context: Dictionary containing 'code', 'file_path', and optionally 'project_name'

        Returns:
            Tuple of (passed: bool, feedback: str)
        """
        ctx = self.extract_context(context, ['code', 'file_path', 'project_name'], {'code': ''})
        code = ctx['code']
        file_path = ctx['file_path']
        project_name = ctx['project_name']

        self.logger.info(f"Reviewing code for: {file_path}")

# If the file is JSON, validate JSON first
        if file_path.endswith('.json'):
            import json
            try:
                parsed = json.loads(code)
            except Exception as e:
                self.logger.warning(f"JSON validation failed: {e}")
                self.log_completion(
                    'qa_failed',
                    project_name=project_name,
                    file_path=file_path,
                    reason='json_invalid',
                    error=str(e)
                )
                return False, f"JSON ERROR: {e}"

            # Additional schema checks for config.json
            if file_path.lower().endswith('config.json') or '/config.json' in file_path.lower():
                missing_keys = [k for k in ('name', 'version', 'settings') if k not in parsed]
                if missing_keys:
                    reason = f"Missing keys: {', '.join(missing_keys)}"
                    self.logger.warning(f"Config JSON missing keys: {missing_keys}")
                    self.log_completion(
                        'qa_failed',
                        project_name=project_name,
                        file_path=file_path,
                        reason='config_missing_keys',
                        missing_keys=missing_keys
                    )
                    return False, f"CONFIG ERROR: {reason}"
                # Ensure settings is an object
                if not isinstance(parsed.get('settings'), dict):
                    reason = "'settings' must be an object"
                    self.logger.warning(f"Config JSON invalid 'settings' type")
                    self.log_completion(
                        'qa_failed',
                        project_name=project_name,
                        file_path=file_path,
                        reason='config_settings_type',
                    )
                    return False, f"CONFIG ERROR: {reason}"

            # For JSON files, do a lightweight review via LLM but don't require Python
            qa_task = f"""JSON CONTENT TO REVIEW:
{code}

FILE: {file_path}

Check that the JSON is properly formatted and seems to include reasonable configuration keys for the task.
Respond with ONE of:
- "PASSED: [brief reason]" if JSON is acceptable
- "FAILED: [specific issues]" if JSON needs revision

REVIEW:"""
        else:
            # First, do basic syntax validation for Python files
            is_valid, syntax_error = validate_python_syntax(code)
            if not is_valid:
                self.logger.warning(f"Syntax validation failed: {syntax_error}")
                self.log_completion(
                    'qa_failed',
                    project_name=project_name,
                    file_path=file_path,
                    reason='syntax_error',
                    error=syntax_error
                )
                return False, f"SYNTAX ERROR: {syntax_error}"

            # Build QA-specific prompt for Python
            qa_task = f"""CODE TO REVIEW:
```python
{code}
```

FILE: {file_path}

Review this code and check for:
1. Syntax errors (already validated)
2. Logic errors or bugs
3. Missing imports
4. Incomplete implementation
5. Code that's only comments/placeholders

Respond with ONE of:
- "PASSED: [brief reason]" if code is acceptable
- "FAILED: [specific issues]" if code needs revision

REVIEW:"""

        # Use minimal context for QA (don't need full PSI)
        psi = "Code Review Mode"

        prompt = self.build_prompt(qa_task, psi)

        # Query the brain
        review = self.query_brain(prompt, temperature=0.2)  # Lower temp for consistent reviews

        # Parse review result
        review_upper = review.upper()
        passed = "PASSED" in review_upper and "FAILED" not in review_upper

        if passed:
            self.logger.info(f"Code passed QA review: {file_path}")
            self.log_completion(
                'qa_passed',
                project_name=project_name,
                file_path=file_path,
                review_summary=review[:100]
            )
        else:
            self.logger.warning(f"Code failed QA review: {file_path}")
            self.log_completion(
                'qa_failed',
                project_name=project_name,
                file_path=file_path,
                reason='quality_issues',
                review=review[:200]
            )

        return passed, review

    def quick_validate(self, code: str, file_path: str = "unknown") -> Tuple[bool, Optional[str]]:
        """
        Quick syntax-only validation without LLM review.

        Args:
            code: The code to validate
            file_path: The file path for logging

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        self.logger.debug(f"Quick validating: {file_path}")

        is_valid, error_msg = validate_python_syntax(code)

        if not is_valid:
            self.logger.warning(f"Quick validation failed for {file_path}: {error_msg}")

        return is_valid, error_msg

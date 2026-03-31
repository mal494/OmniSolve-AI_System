"""
Developer agent (Steve) - Writes executable code.
Uses a handler registry to dispatch file generation by file type.
"""
from typing import Dict, Any, Optional

from .base_agent import BaseAgent
from .handlers import FileTypeRegistry, JSONConfigHandler, JSONHandler, PythonHandler
from ..brain import BrainAPI
from ..exceptions.errors import CodeGenerationError


def _build_default_registry() -> FileTypeRegistry:
    """Build and return the default file type handler registry."""
    registry = FileTypeRegistry()
    # Registration order = priority; first match wins
    registry.register(JSONConfigHandler())   # config.json (checked before generic JSON)
    registry.register(JSONHandler())         # any other .json
    registry.register(PythonHandler())       # .py files
    # GenericHandler is the automatic fallback — no need to register
    return registry


class DeveloperAgent(BaseAgent):
    """
    Developer agent (Steve) responsible for writing executable code.
    Converts logic blueprints into working Python code or config files.
    """

    def __init__(self, brain: Optional[BrainAPI] = None):
        """Initialize the Developer agent (loads Steve.json)."""
        super().__init__("Developer", brain=brain)
        self.registry = _build_default_registry()

    def process(self, task: str, context: Dict[str, Any]) -> str:
        """
        Generate executable code / file content for the given task.

        Args:
            task: The development request
            context: Dictionary containing 'psi', 'blueprint', 'file_path',
                     and optionally 'project_name'

        Returns:
            Generated file content as a string

        Raises:
            CodeGenerationError: If unable to generate valid content
        """
        ctx = self.extract_context(
            context,
            ['psi', 'blueprint', 'file_path', 'project_name'],
            {'psi': '', 'blueprint': ''}
        )
        psi = ctx['psi']
        blueprint = ctx['blueprint']
        file_path = ctx['file_path']
        project_name = ctx['project_name']

        self.logger.info(f"Generating code for: {file_path}")

        # Dispatch to the appropriate handler
        handler = self.registry.get_handler(file_path)

        dev_task, examples = handler.build_task(file_path, blueprint)
        prompt = self.build_prompt(dev_task, psi, examples)

        # Query the brain
        response = self.query_brain(prompt, temperature=0.3)

        # Extract result via the handler
        result = handler.extract_result(response, file_path)

        self.logger.info(f"Generated content for {file_path} ({len(result)} chars)")
        self.log_completion(
            'developer_complete',
            project_name=project_name,
            file_path=file_path,
            code_length=len(result),
            handler=type(handler).__name__,
        )

        return result

    def regenerate_with_feedback(
        self,
        original_task: str,
        context: Dict[str, Any],
        feedback: str,
        previous_code: Optional[str] = None,
    ) -> str:
        """
        Regenerate code with feedback from QA or previous attempt.

        Args:
            original_task: The original task
            context: Original context
            feedback: Feedback on what went wrong
            previous_code: The previous code attempt (if any)

        Returns:
            Regenerated code
        """
        file_path = context.get('file_path', 'unknown')
        self.logger.info(f"Regenerating code for {file_path} with feedback")

        enhanced_task = f"""{original_task}

PREVIOUS ATTEMPT FAILED.
FEEDBACK: {feedback}

{f'PREVIOUS CODE (DO NOT REPEAT):{chr(10)}```python{chr(10)}{previous_code}{chr(10)}```' if previous_code else ''}

Generate IMPROVED code that addresses the feedback.
Write ACTUAL EXECUTABLE CODE, not just comments or placeholders.
"""

        return self.process(enhanced_task, context)

"""
Developer agent (Steve) - Writes executable code.
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..utils.text_parsers import extract_code, validate_python_syntax, extract_json_any
from ..exceptions.errors import CodeGenerationError


class DeveloperAgent(BaseAgent):
    """
    Developer agent (Steve) responsible for writing executable code.
    Converts logic blueprints into working Python code.
    """

    def __init__(self):
        """Initialize the Developer agent (loads Steve.json)."""
        super().__init__("Developer")  # This loads Steve.json

    def process(self, task: str, context: Dict[str, Any]) -> str:
        """
        Generate executable code for the given task.

        Args:
            task: The development request
            context: Dictionary containing 'psi', 'blueprint', 'file_path', and optionally 'project_name'

        Returns:
            Generated Python code

        Raises:
            CodeGenerationError: If unable to generate valid code
        """
        ctx = self.extract_context(context, ['psi', 'blueprint', 'file_path', 'project_name'], {'psi': '', 'blueprint': ''})
        psi = ctx['psi']
        blueprint = ctx['blueprint']
        file_path = ctx['file_path']
        project_name = ctx['project_name']

        self.logger.info(f"Generating code for: {file_path}")

        # Build examples for few-shot learning and adjust by file type
        if file_path.endswith('.py'):
            examples = """
Example Output:
```python
import json

def load_config(path):
    with open(path, 'r') as f:
        return json.load(f)

def main():
    config = load_config('config.json')
    print(f"Loaded: {config}")

if __name__ == '__main__':
    main()
```
"""
            dev_task = f"""LOGIC BLUEPRINT:
{blueprint}

FILE TO IMPLEMENT: {file_path}

TASK: Write executable Python code for '{file_path}'.

CRITICAL RULES:
- Write ONLY code that RUNS
- Do NOT write comments explaining the plan
- Do NOT write "Step 1", "Step 2", etc.
- Output code in a ```python code block
- Include necessary imports
- Follow the logic blueprint

CODE:"""
        elif file_path.endswith('.json'):
            # If this is the main config file, require a minimal schema
            if file_path.lower().endswith('config.json') or '/config.json' in file_path.lower():
                examples = """
Example Output (config JSON):
{
  "name": "project_name",
  "version": "0.1.0",
  "settings": {
    "enabled": true,
    "log_level": "INFO"
  }
}
"""
                dev_task = f"""LOGIC BLUEPRINT:
{blueprint}

FILE TO IMPLEMENT: {file_path}

TASK: Produce the contents of the JSON configuration file '{file_path}'.

CRITICAL RULES:
- Output ONLY the raw JSON content (no markdown, no code fences)
- The JSON must be valid and parseable with json.loads
- The JSON must include the keys: "name" (string), "version" (string), and "settings" (object)
- The settings object should contain sensible defaults (e.g., "enabled": true, "log_level": "INFO")
- Do not include comments or explanatory text

CONTENT:"""
            else:
                examples = """
Example Output (JSON):
{
  "setting": "value",
  "enabled": true
}
"""
                dev_task = f"""LOGIC BLUEPRINT:
{blueprint}

FILE TO IMPLEMENT: {file_path}

TASK: Produce the contents of the JSON file '{file_path}'.

CRITICAL RULES:
- Output ONLY the raw JSON content (no markdown, no code fences)
- The JSON must be valid and parseable with json.loads
- Do not include comments or explanatory text
- Use appropriate keys/values per the blueprint

CONTENT:"""
        else:
            # Generic fallback for other file types: output raw content only
            examples = """
Example Output (raw file content):
<file contents here>
"""
            dev_task = f"""LOGIC BLUEPRINT:
{blueprint}

FILE TO IMPLEMENT: {file_path}

TASK: Produce the file contents for '{file_path}'.

CRITICAL RULES:
- Output ONLY the raw file content (no markdown, no code fences)
- Do not include explanatory text

CONTENT:"""

        prompt = self.build_prompt(dev_task, psi, examples)

        # Query the brain
        response = self.query_brain(prompt, temperature=0.3)

        # Extract result based on expected file type
        if file_path.endswith('.py'):
            code = extract_code(response, validate_non_empty=True)
            if not code:
                self.logger.error(f"Failed to extract code. Response: {response[:200]}")
                raise CodeGenerationError(
                    f"Failed to generate valid code for {file_path}",
                    {'response': response[:500]}
                )
            # Validate syntax
            is_valid, error_msg = validate_python_syntax(code)
            if not is_valid:
                self.logger.warning(f"Generated code has syntax errors: {error_msg}")
            audit_meta = {
                'syntax_valid': is_valid
            }
            result = code
        elif file_path.endswith('.json'):
            # Extract JSON object/array from response
            parsed = extract_json_any(response)
            if parsed is None:
                self.logger.error(f"Failed to extract JSON content. Response: {response[:200]}")
                raise CodeGenerationError(
                    f"Failed to generate valid JSON for {file_path}",
                    {'response': response[:500]}
                )
            # Normalize JSON string
            import json
            result = json.dumps(parsed, indent=2)
            audit_meta = {'json_valid': True}
        else:
            # Generic fallback: strip markdown and take raw block
            # Try code block extraction first, then fallback to stripped response
            content = extract_code(response, validate_non_empty=False)
            if content:
                result = content
            else:
                result = response.strip()
            audit_meta = {'raw': True}

        self.logger.info(f"Generated content for {file_path} ({len(result)} chars)")
        self.log_completion(
            'developer_complete',
            project_name=project_name,
            file_path=file_path,
            code_length=len(result),
            **audit_meta
        )

        return result

    def regenerate_with_feedback(
        self,
        original_task: str,
        context: Dict[str, Any],
        feedback: str,
        previous_code: Optional[str] = None
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

        # Augment the context with feedback
        enhanced_task = f"""{original_task}

PREVIOUS ATTEMPT FAILED.
FEEDBACK: {feedback}

{f'PREVIOUS CODE (DO NOT REPEAT):{chr(10)}```python{chr(10)}{previous_code}{chr(10)}```' if previous_code else ''}

Generate IMPROVED code that addresses the feedback.
Write ACTUAL EXECUTABLE CODE, not just comments or placeholders.
"""

        return self.process(enhanced_task, context)

"""
Architect agent - Designs file structures for projects.
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..utils.text_parsers import extract_json
from ..exceptions.errors import ParsingError


class ArchitectAgent(BaseAgent):
    """
    Architect agent responsible for designing file structures.
    Outputs JSON list of files to create/modify.
    """

    def __init__(self):
        """Initialize the Architect agent."""
        super().__init__("Architect")

    def process(self, task: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Design file structure for the given task.

        Args:
            task: The development request
            context: Dictionary containing 'psi' and optionally 'project_name'

        Returns:
            List of file dictionaries with 'path', 'type', 'action' keys

        Raises:
            ParsingError: If unable to extract valid JSON
        """
        ctx = self.extract_context(context, ['psi', 'project_name'], {'psi': ''})
        psi = ctx['psi']
        project_name = ctx['project_name']

        self.logger.info(f"Designing file structure for: {task[:50]}...")

        # Build examples for few-shot learning
        examples = """
Example Output:
[
  {"path": "main.py", "type": "file", "action": "create"},
  {"path": "utils/helper.py", "type": "file", "action": "create"},
  {"path": "config.json", "type": "file", "action": "create"}
]
"""

        # Build the architect-specific prompt
        arch_task = f"""Task: {task}

Output a valid JSON list of files needed for this project.
Format: [{{"path": "filename", "type": "file", "action": "create"}}]

CRITICAL RULES:
- Output ONLY the JSON list
- Do NOT write explanations before or after the JSON
- Each file must have: path, type, action
- Use forward slashes in paths (e.g., "src/main.py")

JSON OUTPUT:"""

        prompt = self.build_prompt(arch_task, psi, examples)

        # Query the brain
        response = self.query_brain(prompt, temperature=0.2)  # Lower temp for structured output

        # Extract JSON
        file_list = extract_json(response)

        if not file_list:
            self.handle_extraction_error(
                response,
                "Architect failed to generate valid file structure",
                ParsingError
            )

        # Validate structure
        for file_entry in file_list:
            if not all(key in file_entry for key in ['path', 'type', 'action']):
                raise ParsingError(
                    "Invalid file entry format",
                    {'entry': file_entry}
                )

        self.logger.info(f"Generated file structure with {len(file_list)} files")
        self.log_completion(
            'architect_complete',
            project_name=project_name,
            file_count=len(file_list),
            files=[f['path'] for f in file_list]
        )

        return file_list

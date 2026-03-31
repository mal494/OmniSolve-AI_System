"""
Generic catch-all handler for file types not handled by other strategies.
"""
from typing import Tuple

from ...utils.text_parsers import extract_code
from .base_handler import FileTypeHandler

_EXAMPLES = """
Example Output (raw file content):
<file contents here>
"""


class GenericHandler(FileTypeHandler):
    """
    Catch-all handler that accepts any file type.
    Should always be registered last in the registry.
    """

    def can_handle(self, file_path: str) -> bool:
        return True  # Catch-all

    def build_task(self, file_path: str, blueprint: str) -> Tuple[str, str]:
        task = f"""LOGIC BLUEPRINT:
{blueprint}

FILE TO IMPLEMENT: {file_path}

TASK: Produce the file contents for '{file_path}'.

CRITICAL RULES:
- Output ONLY the raw file content (no markdown, no code fences)
- Do not include explanatory text

CONTENT:"""
        return task, _EXAMPLES

    def extract_result(self, response: str, file_path: str) -> str:
        # Try code block first, fall back to stripped raw response
        content = extract_code(response, validate_non_empty=False)
        return content if content else response.strip()

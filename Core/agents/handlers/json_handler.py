"""
Handlers for JSON files.

Two handlers are provided and should be registered in order:
  1. JSONConfigHandler — for files named 'config.json' (requires name/version/settings)
  2. JSONHandler        — for all other .json files
"""
import json
from typing import Tuple

from ...exceptions.errors import CodeGenerationError
from ...utils.text_parsers import extract_json_any
from .base_handler import FileTypeHandler

_CONFIG_EXAMPLES = """
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

_JSON_EXAMPLES = """
Example Output (JSON):
{
  "setting": "value",
  "enabled": true
}
"""


class JSONConfigHandler(FileTypeHandler):
    """Handles config.json files; enforces name/version/settings schema."""

    def can_handle(self, file_path: str) -> bool:
        fp_lower = file_path.lower()
        return fp_lower.endswith('config.json') or '/config.json' in fp_lower

    def build_task(self, file_path: str, blueprint: str) -> Tuple[str, str]:
        task = f"""LOGIC BLUEPRINT:
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
        return task, _CONFIG_EXAMPLES

    def extract_result(self, response: str, file_path: str) -> str:
        parsed = extract_json_any(response)
        if parsed is None:
            raise CodeGenerationError(
                f"Failed to extract valid JSON for {file_path}",
                {'response': response[:500]},
            )
        return json.dumps(parsed, indent=2)


class JSONHandler(FileTypeHandler):
    """Handles generic .json files."""

    def can_handle(self, file_path: str) -> bool:
        return file_path.endswith('.json')

    def build_task(self, file_path: str, blueprint: str) -> Tuple[str, str]:
        task = f"""LOGIC BLUEPRINT:
{blueprint}

FILE TO IMPLEMENT: {file_path}

TASK: Produce the contents of the JSON file '{file_path}'.

CRITICAL RULES:
- Output ONLY the raw JSON content (no markdown, no code fences)
- The JSON must be valid and parseable with json.loads
- Do not include comments or explanatory text
- Use appropriate keys/values per the blueprint

CONTENT:"""
        return task, _JSON_EXAMPLES

    def extract_result(self, response: str, file_path: str) -> str:
        parsed = extract_json_any(response)
        if parsed is None:
            raise CodeGenerationError(
                f"Failed to extract valid JSON for {file_path}",
                {'response': response[:500]},
            )
        return json.dumps(parsed, indent=2)

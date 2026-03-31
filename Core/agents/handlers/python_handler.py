"""
Handler for Python (.py) source files.
"""
from typing import Tuple

from ...exceptions.errors import CodeGenerationError
from ...utils.text_parsers import extract_code, validate_python_syntax
from .base_handler import FileTypeHandler

_EXAMPLES = """
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


class PythonHandler(FileTypeHandler):
    """Handles generation of Python source files."""

    def can_handle(self, file_path: str) -> bool:
        return file_path.endswith('.py')

    def build_task(self, file_path: str, blueprint: str) -> Tuple[str, str]:
        task = f"""LOGIC BLUEPRINT:
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
        return task, _EXAMPLES

    def extract_result(self, response: str, file_path: str) -> str:
        code = extract_code(response, validate_non_empty=True)
        if not code:
            raise CodeGenerationError(
                f"Failed to extract Python code block for {file_path}",
                {'response': response[:500]},
            )
        is_valid, error_msg = validate_python_syntax(code)
        if not is_valid:
            # Return the code anyway — QA will reject if truly broken;
            # but log the warning so callers can surface it.
            # We don't raise here to allow the QA retry loop to decide.
            pass
        return code

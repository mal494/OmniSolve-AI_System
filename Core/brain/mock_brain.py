"""
Mock brain backend for testing.
Returns configurable preset responses without any network calls.
"""
from typing import Dict, List, Optional

from .base_brain import BrainAPI, GenerateResult

# Default mock responses keyed by keyword found in the prompt
_DEFAULT_RESPONSES: Dict[str, str] = {
    "architect": '[{"path": "main.py", "type": "python", "action": "create"}]',
    "planner": "1. Define main function\n2. Implement logic\n3. Add tests",
    "developer": '```python\ndef main():\n    print("Hello, World!")\n\nif __name__ == "__main__":\n    main()\n```',
    "qa": "PASSED: Code looks correct and syntax is valid.",
    "default": "PASSED: Mock response from MockBrainAPI.",
}


class MockBrainAPI(BrainAPI):
    """
    Mock LLM backend that returns preset responses.
    Used for testing without a real LLM running.

    Usage:
        brain = MockBrainAPI()                          # default responses
        brain = MockBrainAPI({"default": "PASSED: ok"}) # custom responses
        brain = MockBrainAPI(call_log=[])               # capture calls
    """

    def __init__(
        self,
        responses: Optional[Dict[str, str]] = None,
        call_log: Optional[list] = None,
    ):
        self._responses = responses if responses is not None else _DEFAULT_RESPONSES.copy()
        self._call_log = call_log  # if provided, each generate() call is appended

    def generate(
        self,
        prompt: str,
        temperature: float,
        max_length: int,
        max_context: int,
        stop_tokens: List[str],
    ) -> GenerateResult:
        if self._call_log is not None:
            self._call_log.append({
                "prompt_length": len(prompt),
                "temperature": temperature,
                "max_length": max_length,
            })

        # Pick response by scanning prompt for known keywords
        prompt_lower = prompt.lower()
        for keyword, response in self._responses.items():
            if keyword != "default" and keyword in prompt_lower:
                return GenerateResult(text=response, tokens_used=len(response.split()), model="mock")

        return GenerateResult(
            text=self._responses.get("default", "PASSED: Mock response."),
            tokens_used=10,
            model="mock",
        )

    def is_available(self) -> bool:
        return True

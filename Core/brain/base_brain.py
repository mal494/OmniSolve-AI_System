"""
Abstract BrainAPI interface and result dataclass.
All LLM backend implementations must inherit from BrainAPI.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GenerateResult:
    """Result returned by a brain backend generate() call."""
    text: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None


class BrainAPI(ABC):
    """Abstract interface for all LLM brain backends."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: float,
        max_length: int,
        max_context: int,
        stop_tokens: List[str],
    ) -> GenerateResult:
        """
        Send a prompt to the LLM and return the generated text.

        Args:
            prompt: The prompt string
            temperature: Sampling temperature (0.0–1.0)
            max_length: Maximum tokens to generate
            max_context: Maximum context window size
            stop_tokens: List of strings that stop generation

        Returns:
            GenerateResult with text and optional metadata

        Raises:
            BrainConnectionError: If the backend is unreachable
            BrainResponseError: If the response is malformed
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this backend is reachable / configured correctly."""

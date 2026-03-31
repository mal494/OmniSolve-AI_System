"""
Abstract base class for file-type handlers in the Developer agent.
"""
from abc import ABC, abstractmethod
from typing import Tuple


class FileTypeHandler(ABC):
    """
    Strategy interface for generating and extracting content by file type.

    Each handler is responsible for:
      1. Deciding which file types it handles (can_handle)
      2. Building the LLM task prompt + examples (build_task)
      3. Extracting and validating the final content from the LLM response (extract_result)
    """

    @abstractmethod
    def can_handle(self, file_path: str) -> bool:
        """Return True if this handler can process the given file path."""

    @abstractmethod
    def build_task(self, file_path: str, blueprint: str) -> Tuple[str, str]:
        """
        Build the task prompt and examples for the LLM.

        Args:
            file_path: Path of the file to generate
            blueprint: Logic blueprint from the Planner agent

        Returns:
            Tuple of (task_prompt, examples_block)
        """

    @abstractmethod
    def extract_result(self, response: str, file_path: str) -> str:
        """
        Extract the final file content from the LLM response.

        Args:
            response: Raw text returned by the LLM
            file_path: Path of the file (for context / validation)

        Returns:
            The extracted file content as a string

        Raises:
            CodeGenerationError: If extraction or validation fails
        """

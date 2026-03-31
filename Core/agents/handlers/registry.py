"""
File type handler registry.
Returns the first registered handler that can_handle() the given file path.
"""
from typing import List

from .base_handler import FileTypeHandler
from .generic_handler import GenericHandler


class FileTypeRegistry:
    """
    Ordered registry of FileTypeHandler instances.

    Handlers are checked in registration order; the first match wins.
    A GenericHandler is always appended as the final fallback.

    Usage:
        registry = FileTypeRegistry()
        registry.register(JSONConfigHandler())
        registry.register(JSONHandler())
        registry.register(PythonHandler())
        # GenericHandler is appended automatically

        handler = registry.get_handler("config.json")  # → JSONConfigHandler
    """

    def __init__(self):
        self._handlers: List[FileTypeHandler] = []
        self._fallback = GenericHandler()

    def register(self, handler: FileTypeHandler) -> None:
        """
        Append a handler to the end of the priority list.

        Args:
            handler: A FileTypeHandler instance (not GenericHandler)
        """
        if isinstance(handler, GenericHandler):
            # Don't double-register the fallback
            return
        self._handlers.append(handler)

    def get_handler(self, file_path: str) -> FileTypeHandler:
        """
        Return the first handler that can process *file_path*.

        Falls back to GenericHandler if no registered handler matches.

        Args:
            file_path: The file path to look up

        Returns:
            A FileTypeHandler instance
        """
        for handler in self._handlers:
            if handler.can_handle(file_path):
                return handler
        return self._fallback

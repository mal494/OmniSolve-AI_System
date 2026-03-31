"""
File type handler strategies for the Developer agent.
"""
from .base_handler import FileTypeHandler
from .generic_handler import GenericHandler
from .json_handler import JSONConfigHandler, JSONHandler
from .python_handler import PythonHandler
from .registry import FileTypeRegistry

__all__ = [
    "FileTypeHandler",
    "FileTypeRegistry",
    "PythonHandler",
    "JSONConfigHandler",
    "JSONHandler",
    "GenericHandler",
]

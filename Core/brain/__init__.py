"""
Brain adapter layer for OmniSolve.
Provides a unified interface for multiple LLM backends.
"""
from .base_brain import BrainAPI, GenerateResult
from .factory import create_brain
from .circuit_breaker import CircuitBreaker, CircuitState
from .mock_brain import MockBrainAPI

__all__ = [
    "BrainAPI",
    "GenerateResult",
    "create_brain",
    "CircuitBreaker",
    "CircuitState",
    "MockBrainAPI",
]

"""
Custom exceptions for OmniSolve system.
Provides better error handling and debugging information.
"""

from typing import Optional


class OmniSolveError(Exception):
    """Base exception for all OmniSolve errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            details: Additional error details for debugging
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation with details if available."""
        if self.details:
            details_str = ', '.join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ConfigurationError(OmniSolveError):
    """Raised when there's a configuration problem."""
    pass


class BrainConnectionError(OmniSolveError):
    """Raised when unable to connect to the AI brain/API."""
    pass


class BrainResponseError(OmniSolveError):
    """Raised when the brain returns an invalid or error response."""
    pass


class CodeGenerationError(OmniSolveError):
    """Raised when code generation fails."""
    pass


class CodeValidationError(OmniSolveError):
    """Raised when generated code fails validation."""
    pass


class ParsingError(OmniSolveError):
    """Raised when unable to parse brain output."""
    pass


class FileOperationError(OmniSolveError):
    """Raised when file operations fail."""
    pass


class ProjectError(OmniSolveError):
    """Raised for project-related errors."""
    pass


class RetryExhaustedError(OmniSolveError):
    """Raised when max retries are exhausted."""

    def __init__(self, operation: str, attempts: int, last_error: Optional[Exception] = None):
        """
        Initialize retry exhausted error.

        Args:
            operation: The operation that failed
            attempts: Number of attempts made
            last_error: The last exception that occurred
        """
        message = f"Max retries ({attempts}) exhausted for operation: {operation}"
        details = {
            'operation': operation,
            'attempts': attempts,
            'last_error': str(last_error) if last_error else None
        }
        super().__init__(message, details)
        self.last_error = last_error


class CircuitOpenError(OmniSolveError):
    """Raised when a request is blocked because the circuit breaker is OPEN."""

    def __init__(self, name: str, retry_in: float = 0.0):
        """
        Initialize circuit open error.

        Args:
            name: Name of the circuit (e.g. 'brain')
            retry_in: Approximate seconds until the circuit may allow retries
        """
        message = (
            f"Circuit breaker '{name}' is OPEN — backend appears unavailable. "
            f"Retry in ~{retry_in:.0f}s."
        )
        super().__init__(message, {'circuit': name, 'retry_in': retry_in})

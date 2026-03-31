"""
Circuit breaker for LLM brain API calls.
Prevents cascading failures when the backend is consistently unavailable.

States:
  CLOSED    — Normal operation; calls pass through
  OPEN      — Backend is failing; calls raise CircuitOpenError immediately
  HALF_OPEN — Cooldown expired; one test call is allowed through
"""
import time
from enum import Enum
from typing import Any, Callable, Optional

from ..exceptions.errors import CircuitOpenError


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Wraps a callable with circuit-breaker logic.

    Args:
        threshold: Number of consecutive failures before opening the circuit
        timeout: Seconds to wait in OPEN state before transitioning to HALF_OPEN
        name: Optional label used in log messages and errors
    """

    def __init__(self, threshold: int = 5, timeout: float = 60.0, name: str = "brain"):
        self._threshold = threshold
        self._timeout = timeout
        self._name = name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> CircuitState:
        self._check_half_open()
        return self._state

    def call(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Call *fn* with *args*/*kwargs* under circuit-breaker protection.

        Raises:
            CircuitOpenError: If the circuit is OPEN (backend is down)
            Any exception raised by *fn* (and records it as a failure)
        """
        self._check_half_open()

        if self._state == CircuitState.OPEN:
            raise CircuitOpenError(
                self._name,
                self._timeout - (time.time() - (self._last_failure_time or 0)),
            )

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def reset(self) -> None:
        """Manually reset the circuit to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_half_open(self) -> None:
        if (
            self._state == CircuitState.OPEN
            and self._last_failure_time is not None
            and (time.time() - self._last_failure_time) >= self._timeout
        ):
            self._state = CircuitState.HALF_OPEN

    def _on_success(self) -> None:
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            # Test call failed — reopen immediately
            self._state = CircuitState.OPEN
        elif self._failure_count >= self._threshold:
            self._state = CircuitState.OPEN

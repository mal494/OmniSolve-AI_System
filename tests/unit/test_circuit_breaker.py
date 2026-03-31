"""
Unit tests for Core.brain.circuit_breaker.CircuitBreaker.
Tests state transitions: CLOSED → OPEN → HALF_OPEN → CLOSED.
"""
import time
import pytest

from Core.brain.circuit_breaker import CircuitBreaker, CircuitState
from Core.exceptions.errors import CircuitOpenError


class TestCircuitBreakerClosed:
    """Tests for normal CLOSED state operation."""

    def test_initial_state_is_closed(self):
        cb = CircuitBreaker(threshold=3, timeout=60)
        assert cb.state == CircuitState.CLOSED

    def test_successful_call_returns_result(self):
        cb = CircuitBreaker(threshold=3, timeout=60)
        result = cb.call(lambda: 42)
        assert result == 42

    def test_successful_call_resets_failure_count(self):
        cb = CircuitBreaker(threshold=3, timeout=60)

        def fail():
            raise ValueError("boom")

        # Two failures — circuit still closed (threshold=3)
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(fail)

        # One success — failure count resets
        cb.call(lambda: None)
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0


class TestCircuitBreakerOpens:
    """Tests for CLOSED → OPEN transition."""

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(threshold=3, timeout=60)

        def fail():
            raise RuntimeError("fail")

        for _ in range(3):
            with pytest.raises(RuntimeError):
                cb.call(fail)

        assert cb.state == CircuitState.OPEN

    def test_open_circuit_raises_circuit_open_error(self):
        cb = CircuitBreaker(threshold=2, timeout=60)

        def fail():
            raise RuntimeError("fail")

        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(fail)

        with pytest.raises(CircuitOpenError):
            cb.call(lambda: "should not reach")

    def test_open_circuit_does_not_call_fn(self):
        cb = CircuitBreaker(threshold=1, timeout=60)
        called = []

        def fail():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            cb.call(fail)

        def track():
            called.append(True)

        with pytest.raises(CircuitOpenError):
            cb.call(track)

        assert called == []  # fn was never called


class TestCircuitBreakerHalfOpen:
    """Tests for OPEN → HALF_OPEN → CLOSED transition."""

    def test_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker(threshold=1, timeout=0.05)  # 50ms timeout

        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

        assert cb.state == CircuitState.OPEN

        time.sleep(0.1)  # exceed timeout
        # Accessing .state triggers the half-open check
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_success_closes_circuit(self):
        cb = CircuitBreaker(threshold=1, timeout=0.05)

        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

        time.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN

        cb.call(lambda: "ok")
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

    def test_half_open_failure_reopens_circuit(self):
        cb = CircuitBreaker(threshold=1, timeout=0.05)

        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail1")))

        time.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN

        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail2")))

        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerReset:
    """Tests for manual reset."""

    def test_reset_clears_open_state(self):
        cb = CircuitBreaker(threshold=1, timeout=60)

        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

    def test_reset_allows_calls_again(self):
        cb = CircuitBreaker(threshold=1, timeout=60)

        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

        cb.reset()
        result = cb.call(lambda: "after reset")
        assert result == "after reset"


class TestCircuitOpenError:
    """Tests for CircuitOpenError exception."""

    def test_message_includes_circuit_name(self):
        err = CircuitOpenError("my_brain", retry_in=30)
        assert "my_brain" in str(err)

    def test_details_contain_retry_in(self):
        err = CircuitOpenError("brain", retry_in=15)
        assert err.details["retry_in"] == 15

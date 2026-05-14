from __future__ import annotations

import time

import pytest

from iperson.pipeline.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerState,
)


class TestCircuitBreaker:
    def test_initial_state_is_closed(self) -> None:
        cb = CircuitBreaker()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0

    def test_record_failure_increments_count(self) -> None:
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=3))
        cb.record_failure()
        assert cb.failure_count == 1
        assert cb.state == CircuitBreakerState.CLOSED

    def test_threshold_triggers_open(self) -> None:
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=2))
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN

    def test_check_raises_when_open(self) -> None:
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1))
        cb.record_failure()
        with pytest.raises(CircuitBreakerError):
            cb.check()

    def test_record_success_resets_closed(self) -> None:
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1))
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0

    def test_open_to_half_open_after_timeout(self) -> None:
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.01))
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        time.sleep(0.02)
        cb.check()
        assert cb.state == CircuitBreakerState.HALF_OPEN

    def test_half_open_success_transitions_to_closed(self) -> None:
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.01))
        cb.record_failure()
        time.sleep(0.02)
        cb.check()
        assert cb.state == CircuitBreakerState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED

    def test_half_open_failure_reopens(self) -> None:
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.01))
        cb.record_failure()
        time.sleep(0.02)
        cb.check()
        assert cb.state == CircuitBreakerState.HALF_OPEN
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
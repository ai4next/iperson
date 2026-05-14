from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 3
    recovery_timeout: float = 30.0  # seconds


class CircuitBreakerError(Exception):
    """Raised when the circuit breaker is OPEN."""


class CircuitBreaker:
    """Tracks failures and breaks the circuit when threshold is exceeded."""

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self.config = config or CircuitBreakerConfig()
        self.state: CircuitBreakerState = CircuitBreakerState.CLOSED
        self.failure_count: int = 0
        self.last_failure_time: float | None = None

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN

    def record_success(self) -> None:
        if self.state in (CircuitBreakerState.OPEN, CircuitBreakerState.HALF_OPEN):
            self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0

    def check(self) -> None:
        """Check if the circuit is open. Transitions OPEN->HALF_OPEN if timeout passed."""
        if self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time is not None:
                elapsed = time.monotonic() - self.last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
        if self.state == CircuitBreakerState.OPEN:
            raise CircuitBreakerError("Circuit breaker is OPEN")
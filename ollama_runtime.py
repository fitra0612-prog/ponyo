"""Shared Ollama scheduling, bounded requests, and circuit breaking."""

import threading
import time
from collections import defaultdict
from typing import Any, Dict

import requests

from structured_logging import structured_logger
from runtime_metrics import runtime_metrics

from config import (
    OLLAMA_URL,
    OLLAMA_REQUEST_TIMEOUT,
    OLLAMA_MAX_ATTEMPTS,
    OLLAMA_FAILURE_THRESHOLD,
    OLLAMA_COOLDOWN_SECONDS,
    OLLAMA_BACKGROUND_GATE_TIMEOUT,
)


class OllamaResourceBusy(TimeoutError):
    """The serialized inference lane is busy; background work should retry later."""


class OllamaCircuitBreaker:
    """Per-model circuit breaker so a failed model cannot stall every chat."""

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 30.0):
        self.failure_threshold = max(1, int(failure_threshold))
        self.cooldown_seconds = max(0.1, float(cooldown_seconds))
        self._failures = defaultdict(int)
        self._opened_at = {}
        self._lock = threading.Lock()

    def allow(self, model: str) -> bool:
        now = time.monotonic()
        with self._lock:
            opened = self._opened_at.get(model)
            if opened is None:
                return True
            if now - opened >= self.cooldown_seconds:
                self._opened_at.pop(model, None)
                self._failures[model] = 0
                return True
            return False

    def record_success(self, model: str) -> None:
        with self._lock:
            self._failures[model] = 0
            self._opened_at.pop(model, None)

    def record_failure(self, model: str) -> None:
        with self._lock:
            self._failures[model] += 1
            if self._failures[model] >= self.failure_threshold:
                self._opened_at[model] = time.monotonic()


class OllamaRuntime:
    """One bounded, serialized inference lane shared by chat and vision.

    Serializing inference avoids loading llama and moondream simultaneously on
    small GPUs. The lock acquisition is bounded, so vision cannot freeze chat.
    """

    def __init__(self, url: str = OLLAMA_URL, timeout: float = OLLAMA_REQUEST_TIMEOUT,
                 max_attempts: int = OLLAMA_MAX_ATTEMPTS, breaker=None):
        self.url = url.rstrip("/")
        self.timeout = max(0.05, float(timeout))
        self.max_attempts = max(1, int(max_attempts))
        self.session = requests.Session()
        self.inference_gate = threading.Lock()
        self.last_request = None
        self.last_error = None
        self.request_count = 0
        self.failure_count = 0
        self.breaker = breaker or OllamaCircuitBreaker(
            OLLAMA_FAILURE_THRESHOLD, OLLAMA_COOLDOWN_SECONDS
        )

    def _gate_timeout(self, lane: str = "chat", gate_timeout: float = None) -> float:
        """Return a bounded wait for the shared inference lane.

        Background work must never occupy the lane while chat is waiting.  Chat
        gets the full request budget; VLM/yapping fail fast and use their cache
        or local fallback instead of creating a convoy behind a slow model load.
        """
        if gate_timeout is not None:
            return max(0.01, float(gate_timeout))
        if lane == "chat":
            return self.timeout
        return min(self.timeout, OLLAMA_BACKGROUND_GATE_TIMEOUT)

    def post_json(
        self, model: str, endpoint: str, payload: Dict[str, Any],
        timeout: float = None, *, lane: str = "chat", gate_timeout: float = None
    ):
        """POST one inference request with lane-aware contention handling."""
        request_timeout = max(0.05, float(timeout if timeout is not None else self.timeout))
        lane_timeout = self._gate_timeout(lane, gate_timeout)
        self.request_count += 1
        self.last_request = time.time()
        if not self.breaker.allow(model):
            structured_logger.warning("ollama_circuit_open", model=model, endpoint=endpoint)
            raise RuntimeError(f"Ollama circuit open for {model}")

        acquired = self.inference_gate.acquire(timeout=lane_timeout)
        if not acquired:
            # Gate contention is scheduler backpressure, not a model failure.
            # Do not increment the model circuit breaker or it can open after
            # several perfectly healthy background deferrals.
            structured_logger.warning(
                "ollama_resource_conflict", model=model, lane=lane,
                timeout=lane_timeout, request_timeout=request_timeout,
            )
            runtime_metrics.increment("ollama_gate_busy")
            raise OllamaResourceBusy("Ollama inference lane is busy")
        try:
            last_error = None
            for _ in range(self.max_attempts):
                started = time.monotonic()
                try:
                    response = self.session.post(
                        f"{self.url}{endpoint}",
                        json=payload,
                        timeout=request_timeout,
                    )
                    if response.status_code >= 500:
                        raise RuntimeError(f"Ollama HTTP {response.status_code}")
                    runtime_metrics.observe(f"ollama_{lane}_latency_ms", (time.monotonic() - started) * 1000)
                    runtime_metrics.increment("ollama_success")
                    self.breaker.record_success(model)
                    self.last_error = None
                    return response
                except Exception as exc:
                    last_error = exc
                    self.last_error = type(exc).__name__
                    self.failure_count += 1
                    runtime_metrics.increment("ollama_failure")
                    self.breaker.record_failure(model)
                    structured_logger.warning(
                        "ollama_timeout" if isinstance(exc, requests.Timeout) else "ollama_request_failed",
                        model=model, endpoint=endpoint, timeout=request_timeout,
                        error=type(exc).__name__,
                    )
            raise last_error
        finally:
            self.inference_gate.release()


class OllamaHealthMonitor:
    """Lightweight health probe; never includes response bodies or credentials."""
    def __init__(self, url: str = OLLAMA_URL, timeout: float = 2.0):
        self.url = url.rstrip("/")
        self.timeout = max(0.05, float(timeout))
        self.last_status = "unknown"
        self.last_checked = 0.0
        self.interval = 30.0
        self._stop = threading.Event()
        self._thread = None

    def start(self, interval: float = 30.0):
        self.interval = max(5.0, float(interval))
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="ponyo-ollama-health")
        self._thread.start()

    def _run(self):
        while not self._stop.wait(self.interval):
            self.check()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        self._thread = None

    def check(self) -> dict:
        started = time.monotonic()
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=self.timeout)
            models = response.json().get("models", []) if response.status_code == 200 else []
            self.last_status = "healthy" if response.status_code == 200 else "degraded"
            result = {"status": self.last_status, "models": len(models), "latency_ms": round((time.monotonic() - started) * 1000, 1)}
        except requests.Timeout:
            self.last_status = "degraded"
            result = {"status": "degraded", "models": 0, "latency_ms": round((time.monotonic() - started) * 1000, 1)}
            structured_logger.warning("ollama_health_timeout", timeout=self.timeout)
        except Exception as exc:
            self.last_status = "offline"
            result = {"status": "offline", "models": 0, "error": type(exc).__name__}
            structured_logger.warning("ollama_health_failed", error=type(exc).__name__)
        self.last_checked = time.time()
        return result


ollama_runtime = OllamaRuntime()
ollama_health = OllamaHealthMonitor()
